"""
抖音平台客户端
"""

import asyncio
import json
import time
import re
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..utils.logger import LoggerMixin
from ..utils.config import Config
from .models import (
    User, ChatMessage, GiftMessage, LikeMessage, FollowMessage,
    Gift, GiftType, LiveRoomInfo, ConnectionStatus, MessageType
)


class DouyinClient(LoggerMixin):
    """抖音客户端"""
    
    def __init__(self, config: Config):
        """
        初始化抖音客户端
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.driver = None
        self.is_logged_in = False
        self.is_connected = False
        self.room_info = None
        self.connection_status = ConnectionStatus()
        
        # 回调函数
        self.message_callbacks: Dict[MessageType, List[Callable]] = {
            MessageType.CHAT: [],
            MessageType.GIFT: [],
            MessageType.LIKE: [],
            MessageType.FOLLOW: [],
        }
        
        # 配置参数
        self.username = config.get('douyin.username')
        self.password = config.get('douyin.password')
        self.room_id = config.get('douyin.room_id')
        self.headless = config.get('douyin.headless', False)
        self.auto_login = config.get('douyin.auto_login', True)
        
        self.logger.info("抖音客户端初始化完成")
    
    async def start(self):
        """启动客户端"""
        try:
            self.logger.info("启动抖音客户端...")
            
            # 初始化浏览器
            await self._init_browser()
            
            # 自动登录
            if self.auto_login:
                await self.login()
            
            self.logger.info("抖音客户端启动成功")
            
        except Exception as e:
            self.logger.error(f"抖音客户端启动失败: {e}")
            raise
    
    async def stop(self):
        """停止客户端"""
        try:
            self.logger.info("停止抖音客户端...")
            
            self.is_connected = False
            
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            self.logger.info("抖音客户端已停止")
            
        except Exception as e:
            self.logger.error(f"停止抖音客户端时出错: {e}")
    
    async def _init_browser(self):
        """初始化浏览器"""
        try:
            self.logger.info("初始化浏览器...")
            
            # Chrome选项
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless')
            
            # 添加常用选项
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 设置用户代理
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 创建驱动
            self.driver = uc.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("浏览器初始化完成")
            
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {e}")
            raise
    
    async def login(self) -> bool:
        """
        登录抖音账号
        
        Returns:
            bool: 是否登录成功
        """
        try:
            self.logger.info("开始登录抖音账号...")
            
            if not self.username or not self.password:
                self.logger.error("用户名或密码未配置")
                return False
            
            # 访问抖音登录页面
            self.driver.get("https://www.douyin.com/")
            await asyncio.sleep(3)
            
            # 检查是否已经登录
            if await self._check_login_status():
                self.logger.info("已经登录，无需重复登录")
                self.is_logged_in = True
                return True
            
            # 点击登录按钮
            try:
                login_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '登录')]"))
                )
                login_btn.click()
                await asyncio.sleep(2)
            except TimeoutException:
                self.logger.warning("未找到登录按钮，尝试其他方式")
            
            # 切换到密码登录
            try:
                password_login = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '密码登录')]"))
                )
                password_login.click()
                await asyncio.sleep(2)
            except TimeoutException:
                self.logger.warning("未找到密码登录选项")
            
            # 输入用户名
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入手机号']"))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                await asyncio.sleep(1)
            except TimeoutException:
                self.logger.error("未找到用户名输入框")
                return False
            
            # 输入密码
            try:
                password_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入密码']"))
                )
                password_input.clear()
                password_input.send_keys(self.password)
                await asyncio.sleep(1)
            except TimeoutException:
                self.logger.error("未找到密码输入框")
                return False
            
            # 点击登录
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '登录') and contains(@class, 'btn')]"))
                )
                submit_btn.click()
                await asyncio.sleep(3)
            except TimeoutException:
                self.logger.error("未找到登录提交按钮")
                return False
            
            # 等待登录完成
            max_wait = 30
            for i in range(max_wait):
                if await self._check_login_status():
                    self.is_logged_in = True
                    self.logger.info("登录成功！")
                    return True
                await asyncio.sleep(1)
            
            self.logger.error("登录超时")
            return False
            
        except Exception as e:
            self.logger.error(f"登录过程中出错: {e}")
            return False
    
    async def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 检查页面中是否有用户头像或用户名等登录标识
            user_elements = self.driver.find_elements(By.XPATH, "//img[contains(@class, 'avatar')]")
            if user_elements:
                return True
            
            # 检查是否有登录按钮（如果有说明未登录）
            login_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), '登录')]")
            return len(login_elements) == 0
            
        except Exception as e:
            self.logger.warning(f"检查登录状态时出错: {e}")
            return False
    
    async def connect_to_room(self, room_url: str = None) -> bool:
        """
        连接到直播间
        
        Args:
            room_url: 直播间URL，如果为空则使用配置中的room_id
            
        Returns:
            bool: 是否连接成功
        """
        try:
            if not self.is_logged_in:
                self.logger.error("请先登录后再连接直播间")
                return False
            
            # 构建直播间URL
            if not room_url:
                if not self.room_id:
                    self.logger.error("未配置直播间ID")
                    return False
                room_url = f"https://live.douyin.com/{self.room_id}"
            
            self.logger.info(f"连接到直播间: {room_url}")
            
            # 访问直播间
            self.driver.get(room_url)
            await asyncio.sleep(5)
            
            # 获取直播间信息
            self.room_info = await self._get_room_info()
            
            if self.room_info:
                self.is_connected = True
                self.connection_status.is_connected = True
                self.connection_status.last_heartbeat = datetime.now()
                self.logger.info(f"成功连接到直播间: {self.room_info.title}")
                return True
            else:
                self.logger.error("获取直播间信息失败")
                return False
                
        except Exception as e:
            self.logger.error(f"连接直播间失败: {e}")
            return False
    
    async def _get_room_info(self) -> Optional[LiveRoomInfo]:
        """获取直播间信息"""
        try:
            # 获取直播间标题
            title_element = self.driver.find_element(By.XPATH, "//h1[@data-e2e='live-title']")
            title = title_element.text if title_element else "未知直播间"
            
            # 获取主播昵称
            owner_element = self.driver.find_element(By.XPATH, "//span[@data-e2e='live-anchor-name']")
            owner_nickname = owner_element.text if owner_element else "未知主播"
            
            # 获取观看人数
            viewer_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'viewer-count')]")
            viewer_count = 0
            if viewer_element:
                viewer_text = viewer_element.text
                # 解析观看人数（可能包含"万"等单位）
                viewer_count = self._parse_count(viewer_text)
            
            room_info = LiveRoomInfo(
                room_id=self.room_id or "unknown",
                title=title,
                owner_nickname=owner_nickname,
                owner_id="unknown",
                viewer_count=viewer_count,
                is_live=True
            )
            
            return room_info
            
        except Exception as e:
            self.logger.warning(f"获取直播间信息时出错: {e}")
            return None
    
    def _parse_count(self, count_text: str) -> int:
        """解析数量文本（如"1.2万"）"""
        try:
            if '万' in count_text:
                number = float(count_text.replace('万', ''))
                return int(number * 10000)
            elif '千' in count_text:
                number = float(count_text.replace('千', ''))
                return int(number * 1000)
            else:
                return int(re.sub(r'[^\d]', '', count_text))
        except:
            return 0
    
    def add_message_callback(self, message_type: MessageType, callback: Callable):
        """
        添加消息回调函数
        
        Args:
            message_type: 消息类型
            callback: 回调函数
        """
        if message_type in self.message_callbacks:
            self.message_callbacks[message_type].append(callback)
            self.logger.info(f"添加 {message_type.value} 消息回调函数")
    
    def remove_message_callback(self, message_type: MessageType, callback: Callable):
        """
        移除消息回调函数
        
        Args:
            message_type: 消息类型
            callback: 回调函数
        """
        if message_type in self.message_callbacks:
            try:
                self.message_callbacks[message_type].remove(callback)
                self.logger.info(f"移除 {message_type.value} 消息回调函数")
            except ValueError:
                pass
    
    async def _trigger_callbacks(self, message_type: MessageType, message: Any):
        """触发回调函数"""
        callbacks = self.message_callbacks.get(message_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                self.logger.error(f"回调函数执行出错: {e}")
    
    def get_connection_status(self) -> ConnectionStatus:
        """获取连接状态"""
        return self.connection_status
    
    def get_room_info(self) -> Optional[LiveRoomInfo]:
        """获取直播间信息"""
        return self.room_info

    async def start_message_listener(self):
        """启动消息监听器"""
        if not self.is_connected:
            self.logger.error("请先连接到直播间")
            return

        self.logger.info("启动消息监听器...")

        # 启动消息监听循环
        asyncio.create_task(self._message_listener_loop())

    async def _message_listener_loop(self):
        """消息监听循环"""
        while self.is_connected:
            try:
                # 监听弹幕消息
                await self._listen_chat_messages()

                # 监听礼物消息
                await self._listen_gift_messages()

                # 监听点赞消息
                await self._listen_like_messages()

                # 更新心跳
                self.connection_status.last_heartbeat = datetime.now()

                # 短暂休眠避免过度占用CPU
                await asyncio.sleep(0.5)

            except Exception as e:
                self.logger.error(f"消息监听出错: {e}")
                await asyncio.sleep(1)

    async def _listen_chat_messages(self):
        """监听弹幕消息"""
        try:
            # 查找新的弹幕元素
            chat_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'webcast-chatroom___item')]"
            )

            # 处理新消息（这里需要实现去重逻辑）
            for element in chat_elements[-5:]:  # 只处理最新的5条消息
                try:
                    # 提取用户信息
                    username_elem = element.find_element(By.XPATH, ".//span[contains(@class, 'username')]")
                    username = username_elem.text if username_elem else "匿名用户"

                    # 提取消息内容
                    content_elem = element.find_element(By.XPATH, ".//span[contains(@class, 'content')]")
                    content = content_elem.text if content_elem else ""

                    if content:  # 只处理有内容的消息
                        # 创建用户对象
                        user = User(
                            user_id=f"douyin_{hash(username)}",
                            nickname=username
                        )

                        # 创建消息对象
                        message = ChatMessage(
                            message_id=f"chat_{int(time.time() * 1000)}_{hash(content)}",
                            user=user,
                            content=content,
                            timestamp=datetime.now()
                        )

                        # 触发回调
                        await self._trigger_callbacks(MessageType.CHAT, message)

                except Exception as e:
                    self.logger.debug(f"处理弹幕消息时出错: {e}")
                    continue

        except Exception as e:
            self.logger.debug(f"监听弹幕消息时出错: {e}")

    async def _listen_gift_messages(self):
        """监听礼物消息"""
        try:
            # 查找礼物消息元素
            gift_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'gift-message')]"
            )

            for element in gift_elements[-3:]:  # 只处理最新的3条礼物消息
                try:
                    # 提取礼物信息（这里需要根据实际页面结构调整）
                    username_elem = element.find_element(By.XPATH, ".//span[contains(@class, 'username')]")
                    username = username_elem.text if username_elem else "匿名用户"

                    gift_name_elem = element.find_element(By.XPATH, ".//span[contains(@class, 'gift-name')]")
                    gift_name = gift_name_elem.text if gift_name_elem else "未知礼物"

                    # 创建用户和礼物对象
                    user = User(
                        user_id=f"douyin_{hash(username)}",
                        nickname=username
                    )

                    gift = Gift(
                        gift_id=f"gift_{hash(gift_name)}",
                        name=gift_name,
                        price=1.0  # 默认价值，实际应该从配置或API获取
                    )

                    # 创建礼物消息对象
                    message = GiftMessage(
                        message_id=f"gift_{int(time.time() * 1000)}_{hash(gift_name)}",
                        user=user,
                        gift=gift,
                        count=1,
                        timestamp=datetime.now()
                    )

                    # 触发回调
                    await self._trigger_callbacks(MessageType.GIFT, message)

                except Exception as e:
                    self.logger.debug(f"处理礼物消息时出错: {e}")
                    continue

        except Exception as e:
            self.logger.debug(f"监听礼物消息时出错: {e}")

    async def _listen_like_messages(self):
        """监听点赞消息"""
        try:
            # 获取当前点赞数
            like_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'like-count')]")
            if like_elem:
                current_likes = self._parse_count(like_elem.text)

                # 检查点赞数是否增加（简单实现）
                if hasattr(self, '_last_like_count'):
                    if current_likes > self._last_like_count:
                        # 创建点赞消息
                        user = User(
                            user_id="system",
                            nickname="系统"
                        )

                        message = LikeMessage(
                            message_id=f"like_{int(time.time() * 1000)}",
                            user=user,
                            count=current_likes - self._last_like_count,
                            timestamp=datetime.now()
                        )

                        # 触发回调
                        await self._trigger_callbacks(MessageType.LIKE, message)

                self._last_like_count = current_likes

        except Exception as e:
            self.logger.debug(f"监听点赞消息时出错: {e}")
