"""
配置管理模块
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""
    
    def __init__(self, config_data: Dict[str, Any]):
        self._data = config_data
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        data = self._data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """返回配置字典"""
        return self._data.copy()


def load_config(config_path: Optional[str] = None) -> Config:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，默认为 config/config.yaml
        
    Returns:
        Config: 配置对象
    """
    if config_path is None:
        config_path = "config/config.yaml"
    
    config_file = Path(config_path)
    
    # 如果配置文件不存在，尝试从示例文件复制
    if not config_file.exists():
        example_file = config_file.parent / "config.example.yaml"
        if example_file.exists():
            logger.warning(f"配置文件 {config_path} 不存在，从示例文件创建")
            import shutil
            shutil.copy(example_file, config_file)
        else:
            raise FileNotFoundError(f"配置文件 {config_path} 和示例文件都不存在")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 环境变量替换
        config_data = _replace_env_vars(config_data)
        
        logger.info(f"配置文件 {config_path} 加载成功")
        return Config(config_data)
        
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        raise


def _replace_env_vars(data: Any) -> Any:
    """递归替换配置中的环境变量"""
    if isinstance(data, dict):
        return {k: _replace_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_env_vars(item) for item in data]
    elif isinstance(data, str):
        # 替换 ${ENV_VAR} 格式的环境变量
        if data.startswith('${') and data.endswith('}'):
            env_var = data[2:-1]
            return os.getenv(env_var, data)
        return data
    else:
        return data


def save_config(config: Config, config_path: Optional[str] = None) -> None:
    """
    保存配置到文件
    
    Args:
        config: 配置对象
        config_path: 配置文件路径
    """
    if config_path is None:
        config_path = "config/config.yaml"
    
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, 
                     allow_unicode=True, indent=2)
        
        logger.info(f"配置文件已保存到 {config_path}")
        
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        raise
