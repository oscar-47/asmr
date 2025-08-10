"""
数据库管理模块
"""

import sqlite3
import asyncio
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.logger import LoggerMixin


class DatabaseManager(LoggerMixin):
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None
        
    async def connect(self):
        """连接数据库"""
        try:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self._connection.commit()
            self.logger.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self.logger.info("数据库连接已关闭")
    
    async def init_tables(self):
        """初始化数据库表结构"""
        try:
            # 音频文件表
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS audio_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    title TEXT,
                    duration REAL,
                    file_size INTEGER,
                    format TEXT,
                    file_path TEXT NOT NULL,
                    tags TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 播放列表表
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 播放列表项目表
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS playlist_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    audio_file_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    volume REAL DEFAULT 1.0,
                    fade_in REAL DEFAULT 0.0,
                    fade_out REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE,
                    FOREIGN KEY (audio_file_id) REFERENCES audio_files (id) ON DELETE CASCADE
                )
            """)
            
            # 礼物映射表
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS gift_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gift_name TEXT NOT NULL UNIQUE,
                    gift_value REAL,
                    audio_file_id INTEGER,
                    priority INTEGER DEFAULT 1,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (audio_file_id) REFERENCES audio_files (id) ON DELETE SET NULL
                )
            """)
            
            # 用户信息表
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    vip_level INTEGER DEFAULT 0,
                    total_gift_value REAL DEFAULT 0.0,
                    interaction_count INTEGER DEFAULT 0,
                    last_seen TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform_user_id, platform)
                )
            """)
            
            # 播放历史表
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audio_file_id INTEGER NOT NULL,
                    trigger_type TEXT,
                    trigger_data TEXT,
                    user_id INTEGER,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (audio_file_id) REFERENCES audio_files (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            """)
            
            # 系统配置表
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_audio_files_category ON audio_files(category)")
            await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_playlist_items_playlist_id ON playlist_items(playlist_id)")
            await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_users_platform ON users(platform)")
            await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_play_history_played_at ON play_history(played_at)")
            
            await self._connection.commit()
            self.logger.info("数据库表结构初始化完成")
            
        except Exception as e:
            self.logger.error(f"数据库表初始化失败: {e}")
            raise
    
    async def execute(self, sql: str, params: tuple = None) -> int:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            int: 影响的行数
        """
        try:
            if params:
                cursor = await self._connection.execute(sql, params)
            else:
                cursor = await self._connection.execute(sql)
            await self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            self.logger.error(f"SQL执行失败: {sql}, 错误: {e}")
            raise
    
    async def fetchone(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        查询单条记录
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            Optional[Dict[str, Any]]: 查询结果
        """
        try:
            if params:
                cursor = await self._connection.execute(sql, params)
            else:
                cursor = await self._connection.execute(sql)
            
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            self.logger.error(f"查询失败: {sql}, 错误: {e}")
            raise
    
    async def fetchall(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        查询多条记录
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            if params:
                cursor = await self._connection.execute(sql, params)
            else:
                cursor = await self._connection.execute(sql)
            
            rows = await cursor.fetchall()
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            self.logger.error(f"查询失败: {sql}, 错误: {e}")
            raise
    
    async def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入数据
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            int: 插入记录的ID
        """
        columns = list(data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        cursor = await self._connection.execute(sql, tuple(data.values()))
        await self._connection.commit()
        return cursor.lastrowid
    
    async def update(self, table: str, data: Dict[str, Any], where: str, params: tuple = None) -> int:
        """
        更新数据
        
        Args:
            table: 表名
            data: 更新的数据字典
            where: WHERE条件
            params: WHERE条件参数
            
        Returns:
            int: 影响的行数
        """
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE {where}"
        
        update_params = list(data.values())
        if params:
            update_params.extend(params)
        
        cursor = await self._connection.execute(sql, tuple(update_params))
        await self._connection.commit()
        return cursor.rowcount
    
    async def delete(self, table: str, where: str, params: tuple = None) -> int:
        """
        删除数据
        
        Args:
            table: 表名
            where: WHERE条件
            params: WHERE条件参数
            
        Returns:
            int: 影响的行数
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        
        if params:
            cursor = await self._connection.execute(sql, params)
        else:
            cursor = await self._connection.execute(sql)
        
        await self._connection.commit()
        return cursor.rowcount
