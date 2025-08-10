"""
播放列表管理器
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..utils.logger import LoggerMixin
from ..core.database import DatabaseManager
from .models import Playlist, PlaylistItem, AudioFile


class PlaylistManager(LoggerMixin):
    """播放列表管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化播放列表管理器
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self.logger.info("播放列表管理器初始化完成")
    
    async def create_playlist(self, name: str, description: str = None) -> Playlist:
        """
        创建播放列表
        
        Args:
            name: 播放列表名称
            description: 描述
            
        Returns:
            Playlist: 创建的播放列表
        """
        playlist = Playlist(
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        playlist.id = await self.db_manager.insert('playlists', {
            'name': playlist.name,
            'description': playlist.description,
            'is_active': playlist.is_active
        })
        
        self.logger.info(f"播放列表创建成功: {name} (ID: {playlist.id})")
        return playlist
    
    async def get_playlist(self, playlist_id: int, include_items: bool = True) -> Optional[Playlist]:
        """
        获取播放列表
        
        Args:
            playlist_id: 播放列表ID
            include_items: 是否包含播放项目
            
        Returns:
            Optional[Playlist]: 播放列表对象
        """
        data = await self.db_manager.fetchone(
            "SELECT * FROM playlists WHERE id = ?", (playlist_id,)
        )
        
        if not data:
            return None
        
        playlist = Playlist.from_dict(data)
        
        if include_items:
            playlist.items = await self._get_playlist_items(playlist_id)
        
        return playlist
    
    async def list_playlists(self, active_only: bool = False) -> List[Playlist]:
        """
        列出播放列表
        
        Args:
            active_only: 是否只返回激活的播放列表
            
        Returns:
            List[Playlist]: 播放列表列表
        """
        sql = "SELECT * FROM playlists"
        params = None
        
        if active_only:
            sql += " WHERE is_active = 1"
        
        sql += " ORDER BY created_at DESC"
        
        data_list = await self.db_manager.fetchall(sql, params)
        return [Playlist.from_dict(data) for data in data_list]
    
    async def update_playlist(self, playlist_id: int, **kwargs) -> bool:
        """
        更新播放列表
        
        Args:
            playlist_id: 播放列表ID
            **kwargs: 更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        if not kwargs:
            return False
        
        rows_affected = await self.db_manager.update(
            'playlists', kwargs, 'id = ?', (playlist_id,)
        )
        
        if rows_affected > 0:
            self.logger.info(f"播放列表更新成功: {playlist_id}")
            return True
        return False
    
    async def delete_playlist(self, playlist_id: int) -> bool:
        """
        删除播放列表
        
        Args:
            playlist_id: 播放列表ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 先删除播放列表项目
            await self.db_manager.delete(
                'playlist_items', 'playlist_id = ?', (playlist_id,)
            )
            
            # 删除播放列表
            rows_affected = await self.db_manager.delete(
                'playlists', 'id = ?', (playlist_id,)
            )
            
            if rows_affected > 0:
                self.logger.info(f"播放列表删除成功: {playlist_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"删除播放列表失败: {e}")
        
        return False
    
    async def add_audio_to_playlist(self, playlist_id: int, audio_file_id: int,
                                   position: int = None, volume: float = 1.0,
                                   fade_in: float = 0.0, fade_out: float = 0.0) -> PlaylistItem:
        """
        添加音频到播放列表
        
        Args:
            playlist_id: 播放列表ID
            audio_file_id: 音频文件ID
            position: 位置（如果为None则添加到末尾）
            volume: 音量
            fade_in: 淡入时间
            fade_out: 淡出时间
            
        Returns:
            PlaylistItem: 播放列表项目
        """
        # 如果没有指定位置，添加到末尾
        if position is None:
            max_position = await self.db_manager.fetchone(
                "SELECT MAX(position) as max_pos FROM playlist_items WHERE playlist_id = ?",
                (playlist_id,)
            )
            position = (max_position['max_pos'] or 0) + 1
        else:
            # 调整其他项目的位置
            await self._adjust_positions(playlist_id, position, 1)
        
        item = PlaylistItem(
            playlist_id=playlist_id,
            audio_file_id=audio_file_id,
            position=position,
            volume=volume,
            fade_in=fade_in,
            fade_out=fade_out,
            created_at=datetime.now()
        )
        
        item.id = await self.db_manager.insert('playlist_items', {
            'playlist_id': item.playlist_id,
            'audio_file_id': item.audio_file_id,
            'position': item.position,
            'volume': item.volume,
            'fade_in': item.fade_in,
            'fade_out': item.fade_out
        })
        
        self.logger.info(f"音频添加到播放列表成功: 播放列表{playlist_id}, 音频{audio_file_id}")
        return item
    
    async def remove_audio_from_playlist(self, playlist_id: int, item_id: int) -> bool:
        """
        从播放列表移除音频
        
        Args:
            playlist_id: 播放列表ID
            item_id: 播放列表项目ID
            
        Returns:
            bool: 是否移除成功
        """
        # 获取项目位置
        item_data = await self.db_manager.fetchone(
            "SELECT position FROM playlist_items WHERE id = ? AND playlist_id = ?",
            (item_id, playlist_id)
        )
        
        if not item_data:
            return False
        
        position = item_data['position']
        
        # 删除项目
        rows_affected = await self.db_manager.delete(
            'playlist_items', 'id = ? AND playlist_id = ?', (item_id, playlist_id)
        )
        
        if rows_affected > 0:
            # 调整其他项目的位置
            await self._adjust_positions(playlist_id, position + 1, -1)
            self.logger.info(f"音频从播放列表移除成功: 项目{item_id}")
            return True
        
        return False
    
    async def reorder_playlist_item(self, playlist_id: int, item_id: int, new_position: int) -> bool:
        """
        重新排序播放列表项目
        
        Args:
            playlist_id: 播放列表ID
            item_id: 播放列表项目ID
            new_position: 新位置
            
        Returns:
            bool: 是否重排成功
        """
        # 获取当前位置
        item_data = await self.db_manager.fetchone(
            "SELECT position FROM playlist_items WHERE id = ? AND playlist_id = ?",
            (item_id, playlist_id)
        )
        
        if not item_data:
            return False
        
        old_position = item_data['position']
        
        if old_position == new_position:
            return True
        
        try:
            # 调整位置
            if old_position < new_position:
                # 向后移动
                await self.db_manager.execute(
                    "UPDATE playlist_items SET position = position - 1 "
                    "WHERE playlist_id = ? AND position > ? AND position <= ?",
                    (playlist_id, old_position, new_position)
                )
            else:
                # 向前移动
                await self.db_manager.execute(
                    "UPDATE playlist_items SET position = position + 1 "
                    "WHERE playlist_id = ? AND position >= ? AND position < ?",
                    (playlist_id, new_position, old_position)
                )
            
            # 更新目标项目位置
            await self.db_manager.update(
                'playlist_items', {'position': new_position}, 
                'id = ?', (item_id,)
            )
            
            self.logger.info(f"播放列表项目重排成功: {item_id} ({old_position} -> {new_position})")
            return True
            
        except Exception as e:
            self.logger.error(f"播放列表项目重排失败: {e}")
            return False
    
    async def set_active_playlist(self, playlist_id: int) -> bool:
        """
        设置激活的播放列表
        
        Args:
            playlist_id: 播放列表ID
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 取消所有播放列表的激活状态
            await self.db_manager.execute(
                "UPDATE playlists SET is_active = 0"
            )
            
            # 激活指定播放列表
            rows_affected = await self.db_manager.update(
                'playlists', {'is_active': True}, 'id = ?', (playlist_id,)
            )
            
            if rows_affected > 0:
                self.logger.info(f"激活播放列表成功: {playlist_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"设置激活播放列表失败: {e}")
        
        return False
    
    async def _get_playlist_items(self, playlist_id: int) -> List[PlaylistItem]:
        """获取播放列表项目"""
        sql = """
            SELECT pi.*, af.filename, af.title, af.duration, af.format, af.file_path
            FROM playlist_items pi
            LEFT JOIN audio_files af ON pi.audio_file_id = af.id
            WHERE pi.playlist_id = ?
            ORDER BY pi.position
        """
        
        data_list = await self.db_manager.fetchall(sql, (playlist_id,))
        items = []
        
        for data in data_list:
            item = PlaylistItem.from_dict(data)
            
            # 构建音频文件对象
            if data.get('filename'):
                item.audio_file = AudioFile(
                    id=data['audio_file_id'],
                    filename=data['filename'],
                    title=data['title'],
                    duration=data['duration'],
                    format=data['format'],
                    file_path=data['file_path']
                )
            
            items.append(item)
        
        return items
    
    async def _adjust_positions(self, playlist_id: int, start_position: int, adjustment: int):
        """调整播放列表项目位置"""
        await self.db_manager.execute(
            "UPDATE playlist_items SET position = position + ? "
            "WHERE playlist_id = ? AND position >= ?",
            (adjustment, playlist_id, start_position)
        )
