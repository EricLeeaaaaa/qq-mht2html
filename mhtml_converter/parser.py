import base64
import re
import os
import hashlib
from typing import List, Dict, Tuple, Optional
from .utils import PerformanceMonitor

class MHTMLParser:
    """MHTML文件解析器，支持解析MHTML格式并提取HTML和图片内容"""

    BOUNDARY = "boundary"
    CHARSET = "charset"
    CONTENT_TYPE = "Content-Type"
    CONTENT_TRANSFER_ENCODING = "Content-Transfer-Encoding"
    CONTENT_LOCATION = "Content-Location"
    FILENAME = "filename="

    def __init__(self, mhtml_content: str = None, decode_images: bool = True):
        self.mhtml_content = mhtml_content
        self.decode_images = decode_images
        self.dataset: List[Tuple[str, str, str]] = []
        self.boundary: Optional[str] = None
        self.performance = PerformanceMonitor()
        self._missing_images: Dict[str, str] = {}
        self._image_paths: Dict[str, str] = {}
        self._image_content_types: Dict[str, str] = {}

    def _generate_image_filename(self, original_name: str, content: str, content_type: str) -> str:
        """生成唯一的图片文件名"""
        # 使用内容的哈希作为文件名的一部分，确保唯一性
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # 获取扩展名
        ext = self._get_image_extension(content_type)
        
        # 清理原始文件名，只保留基本部分
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', original_name)
        safe_name = safe_name.split('/')[-1].split('\\')[-1]  # 只保留文件名部分
        
        # 如果原始名称中有扩展名，去掉它
        safe_name = os.path.splitext(safe_name)[0]
        
        # 组合新的文件名
        return f"{safe_name}_{content_hash}{ext}"

    def _process_part(self, lines: List[str]) -> Tuple[str, str, str]:
        """处理MHTML的单个部分"""
        content_type = ""
        content_location = ""
        content_encoding = ""
        filename = ""
        content_id = ""
        charset = "utf-8"
        content_lines = []
        
        header_done = False
        for line in lines:
            line = line.strip()
            
            if not header_done:
                if line == "":
                    header_done = True
                    continue
                
                line_lower = line.lower()
                if self.CONTENT_TYPE.lower() in line_lower:
                    content_type = self._get_header_value(line)
                elif self.CONTENT_LOCATION.lower() in line_lower:
                    content_location = self._get_header_value(line)
                elif self.CONTENT_TRANSFER_ENCODING.lower() in line_lower:
                    content_encoding = self._get_header_value(line)
                elif self.FILENAME.lower() in line_lower:
                    try:
                        if '"' in line:
                            filename = line.split('="')[1].rstrip('"')
                        elif "'" in line:
                            filename = line.split("='")[1].rstrip("'")
                        else:
                            filename = line.split('=')[1].strip()
                    except IndexError:
                        continue
                elif "content-id" in line_lower:
                    try:
                        content_id = line.split(':')[1].strip().strip('<>') 
                    except IndexError:
                        continue
                elif self.CHARSET.lower() in line_lower:
                    charset = self._get_header_value(line)
            else:
                content_lines.append(line)

        content = '\n'.join(content_lines)
        
        # 根据编码处理内容
        if content_encoding.lower() == 'base64':
            if not content_type.startswith('image/'):
                content = self._decode_base64(content)
        elif content_encoding.lower() == 'quoted-printable':
            content = self._decode_quoted_printable(content)

        # 确定最终的资源标识符
        resource_id = content_id or filename or content_location
        if content_type.startswith('image/'):
            self._image_content_types[resource_id] = content_type

        return content_type, resource_id, content

    def extract_images(self, output_dir: str) -> Dict[str, str]:
        """提取图片到指定目录"""
        os.makedirs(output_dir, exist_ok=True)
        self._image_paths.clear()

        for content_type, name, content in self.dataset:
            if not content_type.startswith("image/") or not name:
                continue

            try:
                # 生成图片文件名
                filename = self._generate_image_filename(name, content, content_type)
                image_path = os.path.join(output_dir, filename)
                
                try:
                    # 清理并解码base64数据
                    content = ''.join(content.split())
                    img_data = base64.b64decode(content)
                    with open(image_path, 'wb') as f:
                        f.write(img_data)
                    self._image_paths[name] = filename  # 只存储文件名，不包含路径
                except Exception as e:
                    self._missing_images[name] = f"Failed to decode/save image: {str(e)}"
                    
            except Exception as e:
                self._missing_images[name] = str(e)

        return self._image_paths

    def _fix_html_paths(self, html_content: str) -> str:
        """修复HTML中的图片路径"""
        for name, filename in self._image_paths.items():
            # 处理各种可能的引用格式
            patterns = [
                f'src="cid:{re.escape(name)}"',
                f'src="{re.escape(name)}"',
                f'src=\'{re.escape(name)}\'',
                f'src="cid:{re.escape(name)}.dat"',
                f'src="{re.escape(name)}.dat"',
                f'src=\'{re.escape(name)}.dat\'',
            ]
            
            for pattern in patterns:
                html_content = re.sub(
                    pattern,
                    f'src="images/{filename}"',
                    html_content,
                    flags=re.IGNORECASE
                )

        return html_content

    def get_html(self, embedded_images: bool = True) -> str:
        """获取HTML内容"""
        html_content = ""
        image_map = {}

        # 首先找到HTML内容
        for content_type, name, content in self.dataset:
            if content_type == "text/html":
                html_content = content
                break

        if not html_content:
            raise ValueError("No HTML content found in MHTML file")

        # 处理图片
        if embedded_images:
            for content_type, name, content in self.dataset:
                if content_type.startswith("image/"):
                    image_map[name] = (content_type, content)

            # 替换图片引用
            for name, (content_type, content) in image_map.items():
                if self.decode_images:
                    data_uri = f"data:{content_type};base64,{content}"
                    html_content = re.sub(
                        f'src="cid:{re.escape(name)}"',
                        f'src="{data_uri}"',
                        html_content,
                        flags=re.IGNORECASE
                    )
                    html_content = re.sub(
                        f'src="{re.escape(name)}"',
                        f'src="{data_uri}"',
                        html_content,
                        flags=re.IGNORECASE
                    )
        else:
            # 修复图片路径
            html_content = self._fix_html_paths(html_content)

        return html_content

    def _find_boundary(self, lines: List[str]) -> Optional[str]:
        """查找MHTML文件中的boundary标识"""
        for line in lines:
            line = line.strip()
            if self.BOUNDARY in line.lower():
                try:
                    if '"' in line:
                        return line.split('="')[1].rstrip('"')
                    elif "'" in line:
                        return line.split("='")[1].rstrip("'")
                    else:
                        return line.split('=')[1].strip()
                except (IndexError, AttributeError):
                    continue
        return None

    def parse(self) -> None:
        """解析MHTML内容"""
        with self.performance.measure("解析MHTML"):
            if not self.mhtml_content:
                raise ValueError("No MHTML content set")

            lines = self.mhtml_content.splitlines()
            self.boundary = self._find_boundary(lines)
            
            if not self.boundary:
                raise ValueError("Could not find boundary in MHTML content")

            current_part = []
            in_content = False

            for line in lines:
                if self.boundary in line:
                    if current_part and in_content:
                        try:
                            part_data = self._process_part(current_part)
                            if part_data[0] or part_data[1]:
                                self.dataset.append(part_data)
                        except Exception as e:
                            print(f"Warning: Failed to process part: {str(e)}")
                    current_part = []
                    in_content = True
                else:
                    if in_content:
                        current_part.append(line)

            if current_part and in_content:
                try:
                    part_data = self._process_part(current_part)
                    if part_data[0] or part_data[1]:
                        self.dataset.append(part_data)
                except Exception as e:
                    print(f"Warning: Failed to process last part: {str(e)}")

    def set_mhtml_content(self, content: str) -> None:
        """设置要解析的MHTML内容"""
        if not content:
            raise ValueError("MHTML content cannot be empty")
        self.mhtml_content = content

    def _decode_base64(self, data: str) -> str:
        """解码Base64编码的内容"""
        try:
            data = ''.join(data.split())
            return base64.b64decode(data.encode()).decode('utf-8', errors='ignore')
        except Exception as e:
            return data

    def _decode_quoted_printable(self, data: str) -> str:
        """解码Quoted-Printable编码的内容"""
        import quopri
        try:
            return quopri.decodestring(data.encode()).decode('utf-8', errors='ignore')
        except Exception as e:
            return data

    def _get_header_value(self, header_line: str) -> str:
        """从头部行中提取值"""
        try:
            value = header_line.split(':', 1)[1].strip()
            return value.rstrip(';').strip()
        except (IndexError, AttributeError):
            return ""

    def _get_image_extension(self, content_type: str) -> str:
        """根据Content-Type获取图片扩展名"""
        type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/bmp': '.bmp',
            'image/x-icon': '.ico',
            'image/vnd.microsoft.icon': '.ico',
            'image/svg+xml': '.svg'
        }
        return type_map.get(content_type.lower(), '.img')

    def get_missing_images(self) -> Dict[str, str]:
        """获取处理失败的图片列表"""
        return self._missing_images.copy()

    def get_performance_stats(self) -> str:
        """获取性能统计信息"""
        return str(self.performance)
