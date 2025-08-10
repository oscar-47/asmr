# ASMR AI 虚拟主播系统

一个基于AI的自动化ASMR虚拟主播系统，支持抖音直播平台集成、智能弹幕回应、礼物识别触发音频播放等功能。

## 功能特性

- 🎵 **ASMR音频播放列表管理** - 支持多种音频格式的导入、管理和播放
- 📱 **抖音平台集成** - 自动连接抖音直播间，监听礼物和弹幕
- 🎁 **智能礼物识别** - 屏幕识别礼物并自动触发相应音频播放
- 🤖 **AI弹幕回应** - 使用AI生成自然的弹幕回应并转换为语音
- 🎚️ **音频混音引擎** - 支持多音频同时播放、音量控制、淡入淡出
- 🌐 **Web管理界面** - 友好的Web界面用于系统配置和监控

## 项目结构

```
asmr-ai/
├── src/                    # 源代码目录
│   ├── core/              # 核心模块
│   ├── platforms/         # 平台集成模块
│   ├── audio/             # 音频处理模块
│   ├── ai/                # AI相关模块
│   ├── web/               # Web界面模块
│   └── utils/             # 工具模块
├── assets/                # 资源文件
│   ├── audio/             # 音频文件存储
│   └── models/            # AI模型文件
├── config/                # 配置文件
├── data/                  # 数据文件
├── logs/                  # 日志文件
├── tests/                 # 测试文件
├── docs/                  # 文档
├── requirements.txt       # Python依赖
├── setup.py              # 安装脚本
└── main.py               # 主程序入口
```

## 快速开始

### 环境要求

- Python 3.9+
- FFmpeg (用于音频处理)
- Chrome/Chromium (用于抖音登录)

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd asmr-ai
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置系统
```bash
cp config/config.example.yaml config/config.yaml
# 编辑配置文件，填入抖音账号等信息
```

5. 运行系统
```bash
python main.py
```

## 配置说明

详细配置说明请参考 [配置文档](docs/configuration.md)

## 开发指南

详细开发指南请参考 [开发文档](docs/development.md)

## 许可证

MIT License
