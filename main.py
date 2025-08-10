#!/usr/bin/env python3
"""
ASMR AI 虚拟主播系统主程序入口
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import ASMRApplication
from src.utils.logger import setup_logger
from src.utils.config import load_config


async def main():
    """主程序入口"""
    try:
        # 设置日志
        logger = setup_logger()
        logger.info("ASMR AI 虚拟主播系统启动中...")
        
        # 加载配置
        config = load_config()
        logger.info("配置文件加载完成")
        
        # 创建应用实例
        app = ASMRApplication(config)
        
        # 启动应用
        await app.start()
        
        # 保持运行
        logger.info("系统启动完成，按 Ctrl+C 退出")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到退出信号，正在关闭系统...")
            await app.stop()
            
    except Exception as e:
        logging.error(f"系统启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 9):
        print("错误: 需要Python 3.9或更高版本")
        sys.exit(1)
    
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("assets/audio", exist_ok=True)
    
    # 运行主程序
    asyncio.run(main())
