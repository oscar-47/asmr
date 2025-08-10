"""
音频文件管理器
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from pydub import AudioSegment
from pydub.utils import mediainfo

from ..utils.logger import LoggerMixin
from ..core.database import DatabaseManager
from .models import AudioFile


class AudioFileManager(LoggerMixin):
    """音频文件管理器"""
    
    # 支持的音频格式
    SUPPORTED_FORMATS = {
        '.mp3': 'mp3',
        '.wav': 'wav',
        '.m4a': 'm4a',
        '.aac': 'aac',
        '.ogg': 'ogg',
        '.flac': 'flac'
    }
    
    def __init__(self, db_manager: DatabaseManager, storage_path: str = "assets/audio"):
        """
        初始化音频文件管理器
        
        Args:
            db_manager: 数据库管理器
            storage_path: 音频文件存储路径
        """
        self.db_manager = db_manager
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"音频文件管理器初始化完成，存储路径: {self.storage_path}")
    
    async def import_audio_file(self, file_path: str, title: str = None, 
                               category: str = None, tags: List[str] = None) -> AudioFile:
        """
        导入音频文件
        
        Args:
            file_path: 源文件路径
            title: 音频标题
            category: 分类
            tags: 标签列表
            
        Returns:
            AudioFile: 导入的音频文件对象
        """
        source_path = Path(file_path)
        
        # 检查文件是否存在
        if not source_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        # 检查文件格式
        if source_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的音频格式: {source_path.suffix}")
        
        try:
            # 获取音频信息
            audio_info = self._get_audio_info(source_path)
            
            # 生成目标文件名
            filename = self._generate_filename(source_path.name)
            target_path = self.storage_path / filename
            
            # 复制文件到存储目录
            shutil.copy2(source_path, target_path)
            
            # 创建音频文件对象
            audio_file = AudioFile(
                filename=filename,
                title=title or source_path.stem,
                duration=audio_info.get('duration'),
                file_size=target_path.stat().st_size,
                format=self.SUPPORTED_FORMATS[source_path.suffix.lower()],
                file_path=str(target_path),
                tags=json.dumps(tags) if tags else None,
                category=category,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            audio_file.id = await self.db_manager.insert('audio_files', {
                'filename': audio_file.filename,
                'title': audio_file.title,
                'duration': audio_file.duration,
                'file_size': audio_file.file_size,
                'format': audio_file.format,
                'file_path': audio_file.file_path,
                'tags': audio_file.tags,
                'category': audio_file.category
            })
            
            self.logger.info(f"音频文件导入成功: {filename}")
            return audio_file
            
        except Exception as e:
            self.logger.error(f"导入音频文件失败: {e}")
            # 清理已复制的文件
            if 'target_path' in locals() and target_path.exists():
                target_path.unlink()
            raise
    
    async def get_audio_file(self, file_id: int) -> Optional[AudioFile]:
        """
        获取音频文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            Optional[AudioFile]: 音频文件对象
        """
        data = await self.db_manager.fetchone(
            "SELECT * FROM audio_files WHERE id = ?", (file_id,)
        )
        
        if data:
            return AudioFile.from_dict(data)
        return None
    
    async def list_audio_files(self, category: str = None, 
                              limit: int = None, offset: int = 0) -> List[AudioFile]:
        """
        列出音频文件
        
        Args:
            category: 分类过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[AudioFile]: 音频文件列表
        """
        sql = "SELECT * FROM audio_files"
        params = []
        
        if category:
            sql += " WHERE category = ?"
            params.append(category)
        
        sql += " ORDER BY created_at DESC"
        
        if limit:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        data_list = await self.db_manager.fetchall(sql, tuple(params) if params else None)
        return [AudioFile.from_dict(data) for data in data_list]
    
    async def update_audio_file(self, file_id: int, **kwargs) -> bool:
        """
        更新音频文件信息
        
        Args:
            file_id: 文件ID
            **kwargs: 更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        if not kwargs:
            return False
        
        # 处理标签
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            kwargs['tags'] = json.dumps(kwargs['tags'])
        
        rows_affected = await self.db_manager.update(
            'audio_files', kwargs, 'id = ?', (file_id,)
        )
        
        if rows_affected > 0:
            self.logger.info(f"音频文件更新成功: {file_id}")
            return True
        return False
    
    async def delete_audio_file(self, file_id: int, delete_file: bool = True) -> bool:
        """
        删除音频文件
        
        Args:
            file_id: 文件ID
            delete_file: 是否删除物理文件
            
        Returns:
            bool: 是否删除成功
        """
        # 获取文件信息
        audio_file = await self.get_audio_file(file_id)
        if not audio_file:
            return False
        
        try:
            # 删除数据库记录
            rows_affected = await self.db_manager.delete(
                'audio_files', 'id = ?', (file_id,)
            )
            
            if rows_affected > 0:
                # 删除物理文件
                if delete_file and audio_file.file_path:
                    file_path = Path(audio_file.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        self.logger.info(f"物理文件已删除: {file_path}")
                
                self.logger.info(f"音频文件删除成功: {file_id}")
                return True
            
        except Exception as e:
            self.logger.error(f"删除音频文件失败: {e}")
        
        return False
    
    async def search_audio_files(self, query: str) -> List[AudioFile]:
        """
        搜索音频文件
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[AudioFile]: 搜索结果
        """
        sql = """
            SELECT * FROM audio_files 
            WHERE title LIKE ? OR filename LIKE ? OR category LIKE ?
            ORDER BY created_at DESC
        """
        search_term = f"%{query}%"
        
        data_list = await self.db_manager.fetchall(
            sql, (search_term, search_term, search_term)
        )
        
        return [AudioFile.from_dict(data) for data in data_list]
    
    def _get_audio_info(self, file_path: Path) -> Dict[str, Any]:
        """
        获取音频文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 音频信息
        """
        try:
            # 使用pydub获取音频信息
            audio = AudioSegment.from_file(str(file_path))
            
            return {
                'duration': len(audio) / 1000.0,  # 转换为秒
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width
            }
        except Exception as e:
            self.logger.warning(f"获取音频信息失败: {e}")
            return {}
    
    def _generate_filename(self, original_name: str) -> str:
        """
        生成唯一的文件名
        
        Args:
            original_name: 原始文件名
            
        Returns:
            str: 生成的文件名
        """
        name_part = Path(original_name).stem
        extension = Path(original_name).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成基础文件名
        base_name = f"{name_part}_{timestamp}{extension}"
        target_path = self.storage_path / base_name
        
        # 如果文件已存在，添加序号
        counter = 1
        while target_path.exists():
            base_name = f"{name_part}_{timestamp}_{counter}{extension}"
            target_path = self.storage_path / base_name
            counter += 1
        
        return base_name
