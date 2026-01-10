"""卡片构建器 - 构建云之家图片卡片消息."""

import logging
from typing import List

logger = logging.getLogger(__name__)


class YunzhijiaCardBuilder:
    """云之家卡片消息构建器

    职责：
    1. 构建图片卡片消息载荷
    2. 处理多图片分卡片逻辑
    3. 生成卡片数据结构
    """

    def __init__(self, template_id: str, max_img_per_card: int):
        """初始化卡片构建器

        Args:
            template_id: 云之家卡片模板 ID
            max_img_per_card: 每个卡片最大图片数量
        """
        self.template_id = template_id
        self.max_img_per_card = max_img_per_card

    def build_card_payloads(self, img_urls: List[str], openid: str) -> List[dict]:
        """构建卡片消息载荷列表

        将图片列表拆分成多个卡片（如果超过单卡最大图片数）。

        Args:
            img_urls: 图片 URL 列表
            openid: 接收人 OpenID

        Returns:
            卡片消息载荷列表

        Examples:
            >>> builder = YunzhijiaCardBuilder("template123", max_img_per_card=3)
            >>> payloads = builder.build_card_payloads(["url1", "url2", "url3", "url4"], "user123")
            >>> len(payloads)
            2  # 4张图片需要2个卡片
        """
        if not img_urls or not self.template_id:
            logger.warning("[CardBuilder] No images or template not configured")
            return []

        img_num = len(img_urls)
        card_num = (img_num + self.max_img_per_card - 1) // self.max_img_per_card

        payloads = []
        for i in range(card_num):
            data_content = self._build_data_content(img_urls, i)
            payload = {
                "msgType": 2,  # 卡片消息
                "param": {
                    "baseInfo": {
                        "templateId": self.template_id,
                        "dataContent": str(data_content)
                    }
                },
                "notifyParams": [{"type": "openIds", "values": [openid]}]
            }
            payloads.append(payload)

        logger.info(f"[CardBuilder] Built {card_num} card(s) for {img_num} image(s)")
        return payloads

    def _build_data_content(self, img_urls: List[str], card_index: int) -> dict:
        """构建单个卡片的 data_content

        云之家卡片格式：
        - bigImageUrl: 第一张图片
        - bigImage1Url: 第二张图片
        - bigImage2Url: 第三张图片
        - ...

        Args:
            img_urls: 图片 URL 列表
            card_index: 当前卡片索引

        Returns:
            卡片数据字典
        """
        data_content = {}
        start_idx = card_index * self.max_img_per_card
        end_idx = min(start_idx + self.max_img_per_card, len(img_urls))

        for j, idx in enumerate(range(start_idx, end_idx)):
            img_url = img_urls[idx]
            if j == 0:
                data_content["bigImageUrl"] = img_url
            else:
                data_content[f"bigImage{j}Url"] = img_url

        return data_content
