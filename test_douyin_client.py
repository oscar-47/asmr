#!/usr/bin/env python3
"""
抖音客户端测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.platforms.douyin_client import DouyinClient
from src.platforms.models import MessageType, ChatMessage, GiftMessage, LikeMessage
from src.utils.config import load_config
from src.utils.logger import setup_logger


class DouyinTestClient:
    """抖音测试客户端"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.config = load_config()
        self.client = DouyinClient(self.config)
        
        # 注册消息回调
        self.client.add_message_callback(MessageType.CHAT, self.on_chat_message)
        self.client.add_message_callback(MessageType.GIFT, self.on_gift_message)
        self.client.add_message_callback(MessageType.LIKE, self.on_like_message)
    
    async def on_chat_message(self, message: ChatMessage):
        """处理弹幕消息"""
        self.logger.info(f"💬 弹幕 | {message.user.nickname}: {message.content}")
    
    async def on_gift_message(self, message: GiftMessage):
        """处理礼物消息"""
        self.logger.info(f"🎁 礼物 | {message.user.nickname} 送出了 {message.gift.name} x{message.count}")
    
    async def on_like_message(self, message: LikeMessage):
        """处理点赞消息"""
        self.logger.info(f"👍 点赞 | 收到 {message.count} 个点赞")
    
    async def test_login_only(self):
        """仅测试登录功能"""
        try:
            self.logger.info("=== 测试抖音登录功能 ===")
            
            # 启动客户端
            await self.client.start()
            
            if self.client.is_logged_in:
                self.logger.info("✅ 登录测试成功！")
                
                # 等待用户确认
                input("按回车键继续测试直播间连接，或按 Ctrl+C 退出...")
                
                # 测试连接直播间
                await self.test_room_connection()
            else:
                self.logger.error("❌ 登录测试失败")
            
        except KeyboardInterrupt:
            self.logger.info("用户中断测试")
        except Exception as e:
            self.logger.error(f"测试过程中出错: {e}")
        finally:
            await self.client.stop()
    
    async def test_room_connection(self):
        """测试直播间连接"""
        try:
            self.logger.info("=== 测试直播间连接 ===")
            
            # 获取直播间URL
            room_url = input("请输入直播间URL（或按回车使用配置中的room_id）: ").strip()
            
            if not room_url and not self.config.get('douyin.room_id'):
                self.logger.error("未提供直播间URL且配置中无room_id")
                return
            
            # 连接直播间
            success = await self.client.connect_to_room(room_url if room_url else None)
            
            if success:
                self.logger.info("✅ 直播间连接成功！")
                
                # 显示直播间信息
                room_info = self.client.get_room_info()
                if room_info:
                    self.logger.info(f"直播间标题: {room_info.title}")
                    self.logger.info(f"主播昵称: {room_info.owner_nickname}")
                    self.logger.info(f"观看人数: {room_info.viewer_count}")
                
                # 启动消息监听
                await self.client.start_message_listener()
                
                self.logger.info("开始监听直播间消息，按 Ctrl+C 停止...")
                
                # 保持运行
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("停止消息监听")
            else:
                self.logger.error("❌ 直播间连接失败")
                
        except Exception as e:
            self.logger.error(f"测试直播间连接时出错: {e}")
    
    async def run_interactive_test(self):
        """运行交互式测试"""
        try:
            self.logger.info("=== 抖音客户端交互式测试 ===")
            
            print("\n请选择测试模式:")
            print("1. 仅测试登录")
            print("2. 测试登录 + 直播间连接")
            print("3. 完整测试（登录 + 连接 + 消息监听）")
            
            choice = input("请输入选择 (1-3): ").strip()
            
            if choice == "1":
                await self.test_login_only()
            elif choice == "2":
                await self.client.start()
                if self.client.is_logged_in:
                    await self.test_room_connection()
                await self.client.stop()
            elif choice == "3":
                await self.run_full_test()
            else:
                self.logger.error("无效选择")
                
        except Exception as e:
            self.logger.error(f"交互式测试出错: {e}")
    
    async def run_full_test(self):
        """运行完整测试"""
        try:
            self.logger.info("=== 完整功能测试 ===")
            
            # 启动客户端
            await self.client.start()
            
            if not self.client.is_logged_in:
                self.logger.error("登录失败，无法继续测试")
                return
            
            # 连接直播间
            room_url = input("请输入直播间URL（或按回车使用配置）: ").strip()
            success = await self.client.connect_to_room(room_url if room_url else None)
            
            if not success:
                self.logger.error("连接直播间失败")
                return
            
            # 启动消息监听
            await self.client.start_message_listener()
            
            self.logger.info("🚀 所有功能启动成功！正在监听消息...")
            self.logger.info("按 Ctrl+C 停止测试")
            
            # 保持运行
            try:
                while True:
                    # 显示连接状态
                    status = self.client.get_connection_status()
                    if status.is_connected:
                        self.logger.debug(f"连接正常，最后心跳: {status.last_heartbeat}")
                    
                    await asyncio.sleep(10)
                    
            except KeyboardInterrupt:
                self.logger.info("用户停止测试")
                
        except Exception as e:
            self.logger.error(f"完整测试出错: {e}")
        finally:
            await self.client.stop()


async def main():
    """主函数"""
    test_client = DouyinTestClient()
    
    # 检查配置
    if not test_client.config.get('douyin.username'):
        print("❌ 错误: 请在 config/config.yaml 中配置抖音用户名和密码")
        print("配置示例:")
        print("douyin:")
        print("  username: 'your_phone_number'")
        print("  password: 'your_password'")
        print("  room_id: 'optional_room_id'")
        return
    
    await test_client.run_interactive_test()


if __name__ == "__main__":
    asyncio.run(main())
