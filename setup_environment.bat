@echo off
echo ========================================
echo ASMR AI 虚拟主播系统环境配置
echo ========================================

echo.
echo 1. 检查conda是否已安装...
conda --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到conda，请先安装Anaconda或Miniconda
    echo 下载地址: https://www.anaconda.com/products/distribution
    pause
    exit /b 1
)
echo conda已安装 ✓

echo.
echo 2. 创建conda环境 'asmr-ai'...
conda env create -f environment.yml
if %errorlevel% neq 0 (
    echo 警告: 环境创建失败，尝试更新现有环境...
    conda env update -f environment.yml
)

echo.
echo 3. 激活环境并安装额外依赖...
call conda activate asmr-ai
if %errorlevel% neq 0 (
    echo 错误: 无法激活环境
    pause
    exit /b 1
)

echo.
echo 4. 安装pip依赖...
pip install -r requirements.txt

echo.
echo 5. 安装系统依赖...
echo 请确保已安装以下系统依赖:
echo - FFmpeg (音频处理)
echo - Tesseract OCR (文字识别)
echo - Chrome/Chromium 浏览器 (抖音登录)

echo.
echo 6. 创建项目目录结构...
if not exist "src" mkdir src
if not exist "src\core" mkdir src\core
if not exist "src\platforms" mkdir src\platforms
if not exist "src\audio" mkdir src\audio
if not exist "src\ai" mkdir src\ai
if not exist "src\web" mkdir src\web
if not exist "src\utils" mkdir src\utils
if not exist "assets" mkdir assets
if not exist "assets\audio" mkdir assets\audio
if not exist "assets\models" mkdir assets\models
if not exist "config" mkdir config
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "tests" mkdir tests
if not exist "docs" mkdir docs

echo.
echo 7. 创建空的__init__.py文件...
echo. > src\__init__.py
echo. > src\core\__init__.py
echo. > src\platforms\__init__.py
echo. > src\audio\__init__.py
echo. > src\ai\__init__.py
echo. > src\web\__init__.py
echo. > src\utils\__init__.py

echo.
echo ========================================
echo 环境配置完成！
echo ========================================
echo.
echo 使用方法:
echo 1. 激活环境: conda activate asmr-ai
echo 2. 运行程序: python main.py
echo 3. 访问Web界面: http://localhost:8000
echo.
echo 注意事项:
echo - 首次运行前请配置 config/config.yaml
echo - 确保抖音账号信息正确填写
echo - 检查音频文件路径设置
echo.
pause
