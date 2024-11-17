import argparse
import os
import sys
import traceback
import json
from typing import List
from .parser import MHTMLParser
from .splitter import MHTMLSplitter
from .utils import FileUtils, PerformanceMonitor

def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MHTML文件转换工具')
    parser.add_argument('input', nargs='?', help='输入的MHTML文件路径（如果不指定则处理当前目录下的所有.mht文件）')
    parser.add_argument('-o', '--output', default='./convert', help='输出目录路径（默认: ./convert）')
    parser.add_argument('-s', '--split-size', type=int, default=40, help='分割大小（MB）（默认: 40）')
    parser.add_argument('--no-split', action='store_true', help='不分割大文件')
    parser.add_argument('--no-images', action='store_true', help='不处理图片')
    parser.add_argument('--embed-images', action='store_true', help='将图片嵌入HTML（base64格式）')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    return parser.parse_args()

def save_debug_info(debug_info: dict, output_dir: str, filename: str) -> None:
    """保存调试信息到文件"""
    debug_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_debug.json")
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(debug_info, f, indent=2, ensure_ascii=False)

def process_single_file(input_path: str, args: argparse.Namespace) -> bool:
    """处理单个MHTML文件"""
    print(f"\n处理文件: {input_path}")
    
    # 初始化性能监控
    performance = PerformanceMonitor()
    file_utils = FileUtils()

    with performance.measure("总处理时间"):
        try:
            # 读取文件内容
            if args.verbose:
                print("正在读取文件...")
            content = file_utils.read_file(input_path)
            
            if args.no_split:
                if args.verbose:
                    print("使用直接转换模式...")
                
                # 不分割文件，直接转换
                parser = MHTMLParser(content, decode_images=not args.no_images)
                
                if args.verbose:
                    print("正在解析MHTML内容...")
                parser.parse()
                
                # 生成输出文件名
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(args.output, f"{base_name}.html")
                
                # 确保输出目录存在
                os.makedirs(args.output, exist_ok=True)
                
                # 如果不嵌入图片，则提取图片到单独文件
                if not args.embed_images and not args.no_images:
                    if args.verbose:
                        print("正在提取图片...")
                    images_dir = os.path.join(args.output, "images")
                    image_paths = parser.extract_images(images_dir)
                    
                    if args.debug:
                        print("\n调试信息：")
                        print(f"找到 {len(image_paths)} 个图片")
                        for name, path in image_paths.items():
                            print(f"- {name} -> images/{path}")

                # 处理HTML内容
                if args.verbose:
                    print("正在生成HTML内容...")
                html_content = parser.get_html(embedded_images=args.embed_images)
                
                # 保存HTML文件
                if args.verbose:
                    print(f"正在保存HTML文件到 {output_path}")
                file_utils.write_file(output_path, html_content)
                
                # 在调试模式下保存详细信息
                if args.debug:
                    debug_info = {
                        'image_paths': parser.extract_images(images_dir),
                        'missing_images': parser.get_missing_images(),
                        'performance': str(parser.get_performance_stats()),
                        'output_file': output_path,
                        'images_dir': images_dir
                    }
                    save_debug_info(debug_info, args.output, os.path.basename(input_path))
                
                # 检查是否有丢失的图片
                missing_images = parser.get_missing_images()
                if missing_images:
                    print("\n警告：以下图片处理失败：")
                    for name, error in missing_images.items():
                        print(f"- {name}: {error}")
            
            else:
                if args.verbose:
                    print("使用分割模式...")
                    
                # 使用分割器处理文件
                splitter = MHTMLSplitter(max_size_mb=args.split_size)
                output_files = splitter.split_file(input_path, args.output)
                
                print(f"\n已生成 {len(output_files)} 个文件：")
                for f in output_files:
                    print(f"- {os.path.basename(f)}")
                
                # 检查是否有丢失的图片
                missing_images = splitter.get_missing_images()
                if missing_images:
                    print("\n警告：以下图片处理失败：")
                    for file_name, errors in missing_images.items():
                        print(f"\n在文件 {file_name} 中：")
                        for error in errors:
                            print(f"- {error}")

        except Exception as e:
            print(f"\n错误：处理文件 {input_path} 时出错：")
            print(f"- {str(e)}")
            if args.verbose or args.debug:
                print("\n详细错误信息：")
                print(traceback.format_exc())
            return False

    # 打印性能报告
    print(f"\n{performance}")
    
    # 在调试模式下显示提示
    if args.debug:
        print("\n调试模式：")
        print(f"- HTML文件已保存到：{output_path}")
        print(f"- 图片文件保存在：{os.path.join(args.output, 'images')}")
        print(f"- 调试信息已保存到：{os.path.join(args.output, os.path.splitext(os.path.basename(input_path))[0] + '_debug.json')}")
    
    return True

def main() -> None:
    """主程序入口"""
    args = parse_args()
    
    success_count = 0
    failure_count = 0
    
    if args.input:
        # 处理指定的文件
        if not os.path.exists(args.input):
            print(f"错误：文件 {args.input} 不存在")
            sys.exit(1)
        if process_single_file(args.input, args):
            success_count += 1
        else:
            failure_count += 1
    else:
        # 处理当前目录下的所有.mht文件
        mht_files = find_mht_files()
        if not mht_files:
            print("错误：当前目录下没有找到.mht文件")
            sys.exit(1)
        
        total_files = len(mht_files)
        print(f"找到 {total_files} 个.mht文件")
        
        for i, mht_file in enumerate(mht_files, 1):
            print(f"\n处理第 {i}/{total_files} 个文件")
            if process_single_file(mht_file, args):
                success_count += 1
            else:
                failure_count += 1

    # 打印最终统计
    print("\n处理完成！")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {failure_count} 个文件")
    
    if failure_count > 0:
        sys.exit(1)

def find_mht_files(directory: str = '.') -> List[str]:
    """查找指定目录下的所有.mht文件"""
    return [f for f in os.listdir(directory) if f.lower().endswith('.mht')]

if __name__ == '__main__':
    main()
