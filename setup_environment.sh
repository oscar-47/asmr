#!/bin/bash

echo "========================================"
echo "ASMR AI 虚拟主播系统环境配置"
echo "========================================"

# 检查conda是否已安装
echo ""
echo "1. 检查conda是否已安装..."
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到conda，请先安装Anaconda或Miniconda"
    echo "下载地址: https://www.anaconda.com/products/distribution"
    exit 1
fi
echo "conda已安装 ✓"

# 创建conda环境
echo ""
echo "2. 创建conda环境 'asmr-ai'..."
if conda env create -f environment.yml; then
    echo "环境创建成功 ✓"
else
    echo "警告: 环境创建失败，尝试更新现有环境..."
    conda env update -f environment.yml
fi

# 激活环境
echo ""
echo "3. 激活环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate asmr-ai

if [ $? -ne 0 ]; then
    echo "错误: 无法激活环境"
    exit 1
fi
echo "环境激活成功 ✓"

# 安装pip依赖
echo ""
echo "4. 安装pip依赖..."
pip install -r requirements.txt

# 检查系统依赖
echo ""
echo "5. 检查系统依赖..."
echo "请确保已安装以下系统依赖:"

# 检查FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo "- FFmpeg: 已安装 ✓"
else
    echo "- FFmpeg: 未安装 ❌"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo "  macOS: brew install ffmpeg"
fi

# 检查Tesseract
if command -v tesseract &> /dev/null; then
    echo "- Tesseract OCR: 已安装 ✓"
else
    echo "- Tesseract OCR: 未安装 ❌"
    echo "  Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-chi-sim"
    echo "  CentOS/RHEL: sudo yum install tesseract tesseract-langpack-chi-sim"
    echo "  macOS: brew install tesseract tesseract-lang"
fi

# 检查Chrome/Chromium
if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null || command -v chromium &> /dev/null; then
    echo "- Chrome/Chromium: 已安装 ✓"
else
    echo "- Chrome/Chromium: 未安装 ❌"
    echo "  请安装Chrome或Chromium浏览器用于抖音登录"
fi

# 创建项目目录结构
echo ""
echo "6. 创建项目目录结构..."
mkdir -p src/{core,platforms,audio,ai,web,utils}
mkdir -p assets/{audio,models}
mkdir -p {config,data,logs,tests,docs}

# 创建__init__.py文件
echo ""
echo "7. 创建Python包文件..."
touch src/__init__.py
touch src/core/__init__.py
touch src/platforms/__init__.py
touch src/audio/__init__.py
touch src/ai/__init__.py
touch src/web/__init__.py
touch src/utils/__init__.py

echo ""
echo "========================================"
echo "环境配置完成！"
echo "========================================"
echo ""
echo "使用方法:"
echo "1. 激活环境: conda activate asmr-ai"
echo "2. 运行程序: python main.py"
echo "3. 访问Web界面: http://localhost:8000"
echo ""
echo "注意事项:"
echo "- 首次运行前请配置 config/config.yaml"
echo "- 确保抖音账号信息正确填写"
echo "- 检查音频文件路径设置"
echo ""
