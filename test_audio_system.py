#!/usr/bin/env python3
"""
音频系统测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager
from src.audio.file_manager import AudioFileManager
from src.audio.playlist_manager import PlaylistManager
from src.utils.logger import setup_logger


async def test_audio_system():
    """测试音频系统"""
    logger = setup_logger()
    logger.info("开始测试音频系统...")
    
    try:
        # 初始化数据库
        db_manager = DatabaseManager("data/test_asmr_ai.db")
        await db_manager.connect()
        await db_manager.init_tables()
        logger.info("数据库初始化完成")
        
        # 初始化音频管理器
        file_manager = AudioFileManager(db_manager)
        playlist_manager = PlaylistManager(db_manager)
        logger.info("音频管理器初始化完成")
        
        # 测试播放列表管理
        logger.info("测试播放列表管理...")
        
        # 创建播放列表
        playlist1 = await playlist_manager.create_playlist(
            "测试播放列表1", "这是一个测试播放列表"
        )
        logger.info(f"创建播放列表成功: {playlist1.name} (ID: {playlist1.id})")
        
        playlist2 = await playlist_manager.create_playlist(
            "ASMR放松音频", "用于放松的ASMR音频集合"
        )
        logger.info(f"创建播放列表成功: {playlist2.name} (ID: {playlist2.id})")
        
        # 列出播放列表
        playlists = await playlist_manager.list_playlists()
        logger.info(f"当前播放列表数量: {len(playlists)}")
        for playlist in playlists:
            logger.info(f"  - {playlist.name}: {playlist.description}")
        
        # 设置激活播放列表
        await playlist_manager.set_active_playlist(playlist1.id)
        logger.info(f"设置激活播放列表: {playlist1.name}")
        
        # 测试音频文件管理
        logger.info("测试音频文件管理...")
        
        # 创建测试音频文件记录（模拟导入）
        from src.audio.models import AudioFile
        from datetime import datetime
        
        test_audio = AudioFile(
            filename="test_audio_1.mp3",
            title="测试音频1",
            duration=120.5,
            file_size=2048000,
            format="mp3",
            file_path="assets/audio/test_audio_1.mp3",
            category="测试",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 手动插入测试数据
        test_audio.id = await db_manager.insert('audio_files', {
            'filename': test_audio.filename,
            'title': test_audio.title,
            'duration': test_audio.duration,
            'file_size': test_audio.file_size,
            'format': test_audio.format,
            'file_path': test_audio.file_path,
            'category': test_audio.category
        })
        logger.info(f"创建测试音频文件: {test_audio.title} (ID: {test_audio.id})")
        
        # 添加音频到播放列表
        item1 = await playlist_manager.add_audio_to_playlist(
            playlist1.id, test_audio.id, volume=0.8
        )
        logger.info(f"添加音频到播放列表成功: 项目ID {item1.id}")
        
        # 获取包含项目的播放列表
        playlist_with_items = await playlist_manager.get_playlist(playlist1.id, include_items=True)
        logger.info(f"播放列表 '{playlist_with_items.name}' 包含 {len(playlist_with_items.items)} 个项目")
        
        for item in playlist_with_items.items:
            if item.audio_file:
                logger.info(f"  - 位置 {item.position}: {item.audio_file.title} (音量: {item.volume})")
        
        # 测试搜索功能
        search_results = await file_manager.search_audio_files("测试")
        logger.info(f"搜索 '测试' 找到 {len(search_results)} 个结果")
        
        # 测试更新播放列表
        await playlist_manager.update_playlist(playlist1.id, description="更新后的描述")
        logger.info("播放列表更新成功")
        
        logger.info("音频系统测试完成！所有功能正常工作。")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        raise
    finally:
        if 'db_manager' in locals():
            await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(test_audio_system())
