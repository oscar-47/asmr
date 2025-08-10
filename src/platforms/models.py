"""
平台相关数据模型
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """消息类型枚举"""
    CHAT = "chat"           # 弹幕消息
    GIFT = "gift"           # 礼物消息
    LIKE = "like"           # 点赞消息
    FOLLOW = "follow"       # 关注消息
    SHARE = "share"         # 分享消息
    ENTER = "enter"         # 进入直播间
    SYSTEM = "system"       # 系统消息


class GiftType(Enum):
    """礼物类型枚举"""
    NORMAL = "normal"       # 普通礼物
    COMBO = "combo"         # 连击礼物
    SPECIAL = "special"     # 特殊礼物


@dataclass
class User:
    """用户信息模型"""
    user_id: str
    nickname: str
    avatar_url: Optional[str] = None
    level: int = 0
    vip_level: int = 0
    is_following: bool = False
    is_moderator: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'level': self.level,
            'vip_level': self.vip_level,
            'is_following': self.is_following,
            'is_moderator': self.is_moderator
        }


@dataclass
class ChatMessage:
    """弹幕消息模型"""
    message_id: str
    user: User
    content: str
    timestamp: datetime
    platform: str = "douyin"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'user': self.user.to_dict(),
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'platform': self.platform
        }


@dataclass
class Gift:
    """礼物信息模型"""
    gift_id: str
    name: str
    icon_url: Optional[str] = None
    price: float = 0.0  # 礼物价值（抖币）
    gift_type: GiftType = GiftType.NORMAL
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'gift_id': self.gift_id,
            'name': self.name,
            'icon_url': self.icon_url,
            'price': self.price,
            'gift_type': self.gift_type.value
        }


@dataclass
class GiftMessage:
    """礼物消息模型"""
    message_id: str
    user: User
    gift: Gift
    count: int = 1
    combo_count: int = 1
    total_value: float = 0.0
    timestamp: datetime = None
    platform: str = "douyin"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.total_value == 0.0:
            self.total_value = self.gift.price * self.count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'user': self.user.to_dict(),
            'gift': self.gift.to_dict(),
            'count': self.count,
            'combo_count': self.combo_count,
            'total_value': self.total_value,
            'timestamp': self.timestamp.isoformat(),
            'platform': self.platform
        }


@dataclass
class LikeMessage:
    """点赞消息模型"""
    message_id: str
    user: User
    count: int = 1
    timestamp: datetime = None
    platform: str = "douyin"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'user': self.user.to_dict(),
            'count': self.count,
            'timestamp': self.timestamp.isoformat(),
            'platform': self.platform
        }


@dataclass
class FollowMessage:
    """关注消息模型"""
    message_id: str
    user: User
    timestamp: datetime = None
    platform: str = "douyin"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'user': self.user.to_dict(),
            'timestamp': self.timestamp.isoformat(),
            'platform': self.platform
        }


@dataclass
class LiveRoomInfo:
    """直播间信息模型"""
    room_id: str
    title: str
    owner_nickname: str
    owner_id: str
    viewer_count: int = 0
    like_count: int = 0
    is_live: bool = True
    cover_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'room_id': self.room_id,
            'title': self.title,
            'owner_nickname': self.owner_nickname,
            'owner_id': self.owner_id,
            'viewer_count': self.viewer_count,
            'like_count': self.like_count,
            'is_live': self.is_live,
            'cover_url': self.cover_url
        }


@dataclass
class ConnectionStatus:
    """连接状态模型"""
    is_connected: bool = False
    last_heartbeat: Optional[datetime] = None
    reconnect_count: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_connected': self.is_connected,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'reconnect_count': self.reconnect_count,
            'error_message': self.error_message
        }
