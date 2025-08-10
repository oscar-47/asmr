"""
日志系统配置模块
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import colorlog


def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_file: 日志文件路径
        max_bytes: 单个日志文件最大大小
        backup_count: 备份文件数量
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    if name is None:
        name = "asmr-ai"
    
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # 创建日志目录
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 控制台处理器（彩色输出）
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    
    # 文件处理器（轮转日志）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # 防止日志重复
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)


class LoggerMixin:
    """日志混入类，为其他类提供日志功能"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志器"""
        return logging.getLogger(self.__class__.__name__)


# 设置第三方库的日志级别
def configure_third_party_loggers():
    """配置第三方库的日志级别"""
    # 设置一些常见第三方库的日志级别
    third_party_loggers = [
        'urllib3.connectionpool',
        'selenium.webdriver.remote.remote_connection',
        'websockets.protocol',
        'asyncio',
        'aiohttp.access'
    ]
    
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


# 异常处理装饰器
def log_exceptions(logger: Optional[logging.Logger] = None):
    """
    异常日志装饰器
    
    Args:
        logger: 日志器，如果为None则使用默认日志器
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.exception(f"函数 {func.__name__} 执行出错: {e}")
                else:
                    logging.exception(f"函数 {func.__name__} 执行出错: {e}")
                raise
        return wrapper
    return decorator


# 异步异常处理装饰器
def log_async_exceptions(logger: Optional[logging.Logger] = None):
    """
    异步异常日志装饰器
    
    Args:
        logger: 日志器，如果为None则使用默认日志器
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.exception(f"异步函数 {func.__name__} 执行出错: {e}")
                else:
                    logging.exception(f"异步函数 {func.__name__} 执行出错: {e}")
                raise
        return wrapper
    return decorator
