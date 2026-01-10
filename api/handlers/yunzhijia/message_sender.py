"""消息发送器 - 发送云之家消息（文本和图片卡片）."""

import logging
from typing import List

import aiohttp

from api.handlers.yunzhijia.card_builder import YunzhijiaCardBuilder

logger = logging.getLogger(__name__)


class YunzhijiaMessageSender:
    """云之家消息发送器

    职责：
    1. 发送文本消息到云之家
    2. 发送图片卡片消息
    3. 封装 HTTP 请求逻辑
    """

    def __init__(self, notify_url_template: str):
        """初始化消息发送器

        Args:
            notify_url_template: 云之家通知 URL 模板（包含 {} 占位符用于 token）
                例如: "https://www.yunzhijia.com/gateway/robot/webhook/send?yzjtype=0&yzjtoken={}"
        """
        self.notify_url_template = notify_url_template

    async def send_text(self, token: str, openid: str, content: str):
        """发送文本消息

        Args:
            token: 云之家机器人 token
            openid: 接收人 OpenID
            content: 消息内容
        """
        url = self.notify_url_template.format(token)
        data = {
            "content": content,
            "notifyParams": [{"type": "openIds", "values": [openid]}]
        }

        success = await self._send_request(url, data)
        if success:
            logger.info(f"[MessageSender] Text message sent to {openid}")
        else:
            logger.error(f"[MessageSender] Failed to send text message to {openid}")

    async def send_with_images(
        self,
        token: str,
        openid: str,
        content: str,
        service_base_url: str,
        card_builder: YunzhijiaCardBuilder
    ):
        """发送带图片的消息（文本 + 卡片）

        从内容中提取图片，发送文本消息 + 图片卡片。

        Args:
            token: 云之家机器人 token
            openid: 接收人 OpenID
            content: 消息内容（可能包含 markdown 图片）
            service_base_url: 服务基础 URL（用于图片链接转换）
            card_builder: 卡片构建器实例
        """
        from api.utils.image_utils import extract_images_from_content

        # 提取图片并清理内容
        cleaned_content, img_urls = extract_images_from_content(content, service_base_url)

        # 如果有图片，提示用户
        if img_urls:
            cleaned_content += "\n\n（具体图片请查看下方消息）"

        # 发送文本消息
        await self.send_text(token, openid, cleaned_content)

        # 发送图片卡片
        if img_urls:
            await self._send_card_notices(token, openid, img_urls, card_builder)

    async def _send_card_notices(
        self,
        token: str,
        openid: str,
        img_urls: List[str],
        card_builder: YunzhijiaCardBuilder
    ):
        """发送图片卡片消息列表

        Args:
            token: 云之家机器人 token
            openid: 接收人 OpenID
            img_urls: 图片 URL 列表
            card_builder: 卡片构建器实例
        """
        payloads = card_builder.build_card_payloads(img_urls, openid)
        url = self.notify_url_template.format(token)

        for i, payload in enumerate(payloads):
            success = await self._send_request(url, payload)
            if success:
                logger.info(f"[MessageSender] Card {i+1}/{len(payloads)} sent to {openid}")
            else:
                logger.error(f"[MessageSender] Failed to send card {i+1}/{len(payloads)}")

    async def _send_request(self, url: str, data: dict) -> bool:
        """发送 HTTP 请求到云之家

        Args:
            url: 请求 URL
            data: 请求数据

        Returns:
            是否成功
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"[MessageSender] HTTP {response.status}: {response_text}")
                        return False
        except Exception as e:
            logger.error(f"[MessageSender] Request error: {e}", exc_info=True)
            return False
