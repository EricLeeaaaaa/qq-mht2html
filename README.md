# MHTML 转换工具

这是一个强大的MHTML文件转换工具，支持将MHTML文件转换为HTML文件，并能够处理图片资源。该工具结合了多种实现的优点，提供了灵活的配置选项。

## 主要特性

- 支持将MHTML文件转换为HTML文件
- 自动提取和处理图片资源
- 支持大文件智能分割
- 支持图片嵌入（base64格式）或独立保存
- 提供详细的性能监控报告
- 支持批量处理多个文件
- 自动处理文件编码
- 提供丢失图片的详细提示

## 安装要求

- Python 3.6 或更高版本
- psutil 库（用于性能监控）

## 安装方法

```bash
# 安装依赖
pip install psutil

# 克隆项目后在项目目录运行
pip install -e .
```

## 使用方法

```bash
# 处理单个文件（默认40MB分割）
python -m mhtml_converter your_file.mht

# 处理当前目录下所有.mht文件
python -m mhtml_converter

# 自定义分割大小（单位：MB）
python -m mhtml_converter -s 20 your_file.mht

# 不分割文件
python -m mhtml_converter --no-split your_file.mht

# 将图片嵌入HTML（base64格式）
python -m mhtml_converter --embed-images your_file.mht

# 不处理图片
python -m mhtml_converter --no-images your_file.mht

# 指定输出目录
python -m mhtml_converter -o output_dir your_file.mht
```

## 命令行参数

- `input`: 输入的MHTML文件路径（可选，如果不指定则处理当前目录下所有.mht文件）
- `-o, --output`: 输出目录路径（默认: ./convert）
- `-s, --split-size`: 分割大小（MB）（默认: 40）
- `--no-split`: 不分割大文件
- `--no-images`: 不处理图片
- `--embed-images`: 将图片嵌入HTML（base64格式）

## 输出结果

- 转换后的HTML文件将保存在指定的输出目录中
- 图片文件将保存在 `输出目录/images` 目录下（除非使用了`--embed-images`选项）
- 如果启用了文件分割，将生成多个HTML文件
- 程序会显示详细的执行时间和内存使用情况

## 注意事项

1. 确保有足够的磁盘空间存储转换后的文件
2. 对于特别大的MHTML文件，建议适当调整分割大小
3. 使用`--embed-images`选项会增加生成的HTML文件大小
4. 程序会自动创建必要的目录结构
5. 如果遇到编码问题，程序会自动尝试多种编码方式

## 性能优化

- 使用生成器处理大文件，减少内存占用
- 智能分块处理，避免一次性加载过大内容
- 并提供详细的性能统计信息

## 联系方式

如有问题或建议，请提交Issue或Pull Request。

## 许可证

MIT License
