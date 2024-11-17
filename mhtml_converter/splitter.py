import os
from typing import List, Dict, Optional
from .parser import MHTMLParser
from .utils import FileUtils, PerformanceMonitor

class MHTMLSplitter:
    """MHTML文件分割器，支持将大型MHTML文件分割成多个较小的HTML文件"""

    def __init__(self, max_size_mb: int = 40):
        """
        初始化分割器
        
        Args:
            max_size_mb: 每个分割文件的最大大小（MB）
        """
        self.max_size_mb = max_size_mb
        self.performance = PerformanceMonitor()
        self.file_utils = FileUtils()
        self.missing_images: Dict[str, List[str]] = {}

    def split_file(self, input_path: str, output_dir: str = "./convert") -> List[str]:
        """
        分割MHTML文件
        
        Args:
            input_path: 输入文件路径
            output_dir: 输出目录
        
        Returns:
            List[str]: 生成的文件路径列表
        """
        with self.performance.measure("分割文件"):
            # 创建输出目录
            images_dir = os.path.join(output_dir, "images")
            os.makedirs(images_dir, exist_ok=True)

            # 读取原始文件
            mhtml_content = self.file_utils.read_file(input_path)
            parser = MHTMLParser(mhtml_content)
            parser.parse()

            # 提取基本信息
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            html_content = parser.get_html(embedded_images=False)
            
            # 提取所有图片
            image_paths = parser.extract_images(images_dir)
            self._update_missing_images(parser.get_missing_images(), base_name)

            # 检查文件大小
            if len(mhtml_content) / (1024 * 1024) <= self.max_size_mb:
                # 如果文件较小，直接保存
                output_path = os.path.join(output_dir, f"{base_name}.html")
                self._save_html_file(output_path, html_content, image_paths)
                return [output_path]

            # 分割大文件
            return self._split_large_file(html_content, base_name, output_dir, image_paths)

    def _split_large_file(self, html_content: str, base_name: str, output_dir: str, 
                         image_paths: Dict[str, str]) -> List[str]:
        """处理大文件分割"""
        output_files = []
        current_size = 0
        current_content = []
        file_counter = 1

        # 提取头部模板
        header_template = self._extract_header_template(html_content)
        
        # 分析每行内容
        for line in html_content.split('\n'):
            line_size = len(line.encode('utf-8'))
            image_size = self._calculate_line_images_size(line, image_paths)
            
            # 检查是否需要创建新文件
            if current_size + line_size + image_size > self.max_size_mb * 1024 * 1024:
                # 保存当前文件
                output_path = os.path.join(output_dir, f"{base_name}_{file_counter}.html")
                self._save_html_file(output_path, 
                                   self._build_html_content(header_template, current_content),
                                   image_paths)
                output_files.append(output_path)
                
                # 重置计数器
                current_content = []
                current_size = 0
                file_counter += 1
            
            current_content.append(line)
            current_size += line_size + image_size

        # 保存最后一个文件
        if current_content:
            output_path = os.path.join(output_dir, f"{base_name}_{file_counter}.html")
            self._save_html_file(output_path,
                               self._build_html_content(header_template, current_content),
                               image_paths)
            output_files.append(output_path)

        return output_files

    def _extract_header_template(self, html_content: str) -> str:
        """提取HTML头部模板"""
        import re
        match = re.search(r'(<html.*?<body.*?>)', html_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return "<html><body>"

    def _build_html_content(self, header: str, content: List[str]) -> str:
        """构建完整的HTML内容"""
        return f"{header}\n{''.join(content)}\n</body></html>"

    def _calculate_line_images_size(self, line: str, image_paths: Dict[str, str]) -> int:
        """计算行中包含的图片大小"""
        total_size = 0
        for img_name, img_path in image_paths.items():
            if img_name in line and os.path.exists(img_path):
                total_size += os.path.getsize(img_path)
        return total_size

    def _save_html_file(self, output_path: str, content: str, image_paths: Dict[str, str]) -> None:
        """保存HTML文件，更新图片路径"""
        # 更新图片路径
        for img_name, img_path in image_paths.items():
            relative_path = os.path.join("images", os.path.basename(img_path))
            content = content.replace(f'cid:{img_name}', relative_path)
            content = content.replace(f'"{img_name}"', f'"{relative_path}"')

        # 保存文件
        self.file_utils.write_file(output_path, content)

    def _update_missing_images(self, missing_images: Dict[str, str], file_name: str) -> None:
        """更新丢失的图片信息"""
        if missing_images:
            self.missing_images[file_name] = [
                f"{name}: {error}" for name, error in missing_images.items()
            ]

    def get_missing_images(self) -> Dict[str, List[str]]:
        """获取所有丢失的图片信息"""
        return self.missing_images.copy()

    def get_performance_stats(self) -> str:
        """获取性能统计信息"""
        return str(self.performance)
