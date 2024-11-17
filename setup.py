from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mhtml-converter",
    version="1.0.0",
    author="Cline",
    description="一个功能强大的MHTML文件转换工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mhtml-converter",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "psutil>=5.7.0",
    ],
    entry_points={
        "console_scripts": [
            "mhtml-converter=mhtml_converter.__main__:main",
        ],
    },
)
