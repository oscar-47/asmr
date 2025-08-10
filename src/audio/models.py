"""
音频相关数据模型
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path


@dataclass
class AudioFile:
    """音频文件模型"""
    id: Optional[int] = None
    filename: str = ""
    title: Optional[str] = None
    duration: Optional[float] = None  # 秒
    file_size: Optional[int] = None  # 字节
    format: Optional[str] = None
    file_path: str = ""
    tags: Optional[str] = None  # JSON字符串
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'title': self.title,
            'duration': self.duration,
            'file_size': self.file_size,
            'format': self.format,
            'file_path': self.file_path,
            'tags': self.tags,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioFile':
        """从字典创建实例"""
        return cls(
            id=data.get('id'),
            filename=data.get('filename', ''),
            title=data.get('title'),
            duration=data.get('duration'),
            file_size=data.get('file_size'),
            format=data.get('format'),
            file_path=data.get('file_path', ''),
            tags=data.get('tags'),
            category=data.get('category'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class Playlist:
    """播放列表模型"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List['PlaylistItem'] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Playlist':
        """从字典创建实例"""
        playlist = cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description'),
            is_active=data.get('is_active', False),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
        
        # 加载播放列表项目
        if 'items' in data:
            playlist.items = [PlaylistItem.from_dict(item) for item in data['items']]
        
        return playlist


@dataclass
class PlaylistItem:
    """播放列表项目模型"""
    id: Optional[int] = None
    playlist_id: Optional[int] = None
    audio_file_id: Optional[int] = None
    position: int = 0
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    created_at: Optional[datetime] = None
    audio_file: Optional[AudioFile] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'audio_file_id': self.audio_file_id,
            'position': self.position,
            'volume': self.volume,
            'fade_in': self.fade_in,
            'fade_out': self.fade_out,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'audio_file': self.audio_file.to_dict() if self.audio_file else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaylistItem':
        """从字典创建实例"""
        item = cls(
            id=data.get('id'),
            playlist_id=data.get('playlist_id'),
            audio_file_id=data.get('audio_file_id'),
            position=data.get('position', 0),
            volume=data.get('volume', 1.0),
            fade_in=data.get('fade_in', 0.0),
            fade_out=data.get('fade_out', 0.0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )
        
        # 加载音频文件信息
        if 'audio_file' in data and data['audio_file']:
            item.audio_file = AudioFile.from_dict(data['audio_file'])
        
        return item


@dataclass
class PlaybackState:
    """播放状态模型"""
    is_playing: bool = False
    current_playlist_id: Optional[int] = None
    current_item_id: Optional[int] = None
    current_position: float = 0.0  # 当前播放位置（秒）
    volume: float = 1.0
    is_muted: bool = False
    repeat_mode: str = "none"  # none, single, playlist
    shuffle: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_playing': self.is_playing,
            'current_playlist_id': self.current_playlist_id,
            'current_item_id': self.current_item_id,
            'current_position': self.current_position,
            'volume': self.volume,
            'is_muted': self.is_muted,
            'repeat_mode': self.repeat_mode,
            'shuffle': self.shuffle
        }
