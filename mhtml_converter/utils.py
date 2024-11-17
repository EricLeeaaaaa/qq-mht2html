import os
import time
import psutil
from typing import Any, Optional
from contextlib import contextmanager

class PerformanceMonitor:
    """性能监控工具，用于跟踪执行时间和内存使用情况"""

    def __init__(self):
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss
        self.measurements = {}

    @contextmanager
    def measure(self, name: str):
        """
        测量代码块的执行时间和内存使用
        
        Args:
            name: 测量名称
        """
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            self.measurements[name] = {
                'time': end_time - start_time,
                'memory_delta': end_memory - start_memory
            }

    def get_total_time(self) -> float:
        """获取总执行时间"""
        return time.time() - self.start_time

    def get_memory_usage(self) -> int:
        """获取当前内存使用量"""
        return psutil.Process().memory_info().rss - self.start_memory

    def get_peak_memory(self) -> int:
        """获取峰值内存使用量"""
        return psutil.Process().memory_info().rss

    def _format_size(self, size: int) -> str:
        """格式化大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def __str__(self) -> str:
        """生成性能报告"""
        report = [
            "性能统计报告:",
            f"总执行时间: {self.get_total_time():.3f} 秒",
            f"内存使用增量: {self._format_size(self.get_memory_usage())}",
            f"内存使用峰值: {self._format_size(self.get_peak_memory())}",
            "\n详细测量结果:"
        ]

        for name, data in self.measurements.items():
            report.append(f"- {name}:")
            report.append(f"  执行时间: {data['time']:.3f} 秒")
            report.append(f"  内存变化: {self._format_size(data['memory_delta'])}")

        return "\n".join(report)


class FileUtils:
    """文件操作工具类"""

    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
        
        Returns:
            str: 文件内容
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            encodings = ['gbk', 'gb2312', 'big5', 'latin1']
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            # 如果所有编码都失败，使用二进制模式读取
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')

    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> None:
        """
        写入文件内容
        
        Args:
            file_path: 文件路径
            content: 要写入的内容
            encoding: 文件编码
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)

    @staticmethod
    def ensure_directory(directory: str) -> None:
        """
        确保目录存在
        
        Args:
            directory: 目录路径
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
        
        Returns:
            int: 文件大小（字节）
        """
        return os.path.getsize(file_path)

    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        获取安全的文件名
        
        Args:
            filename: 原始文件名
        
        Returns:
            str: 安全的文件名
        """
        import re
        # 移除非法字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 确保文件名不为空
        if not safe_name:
            safe_name = 'unnamed_file'
        return safe_name
