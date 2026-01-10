"""标签提取器 - 从消息内容中提取特定 XML 标签."""

import re
from typing import List


class TagExtractor:
    """提取消息中的特定标签内容

    用于从 Agent 输出中提取 <reply> 和 <ask> 标签，
    过滤中间思考过程，只保留面向用户的内容。
    """

    @staticmethod
    def extract_tags(content: str, tag_name: str) -> List[str]:
        """从内容中提取指定标签的内容

        Args:
            content: 消息内容
            tag_name: 标签名称（不包含尖括号）

        Returns:
            提取的内容列表（可能有多个相同标签）

        Examples:
            >>> TagExtractor.extract_tags("<reply>你好</reply>", "reply")
            ['你好']
            >>> TagExtractor.extract_tags("<ask>请问</ask><ask>如何</ask>", "ask")
            ['请问', '如何']
        """
        pattern = rf'<{tag_name}>(.*?)</{tag_name}>'
        matches = re.findall(pattern, content, re.DOTALL)
        return [m.strip() for m in matches if m.strip()]

    @staticmethod
    def extract_replies(content: str) -> List[str]:
        """提取 <reply> 标签内容

        用于提取 Agent 的最终回复内容。
        SKILL 规定最终答案必须包裹在 <reply> 标签中。

        Args:
            content: Agent 输出的消息内容

        Returns:
            回复内容列表
        """
        return TagExtractor.extract_tags(content, "reply")

    @staticmethod
    def extract_asks(content: str) -> List[str]:
        """提取 <ask> 标签内容

        用于提取需要用户回复的交互式问题。
        SKILL 规定询问用户的内容必须包裹在 <ask> 标签中。

        Args:
            content: Agent 输出的消息内容

        Returns:
            问题内容列表
        """
        return TagExtractor.extract_tags(content, "ask")
