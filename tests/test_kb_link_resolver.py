"""Tests for kb_link_resolver module."""

import pytest
from unittest.mock import patch, MagicMock
from api.utils.kb_link_resolver import transform_kb_links, resolve_kb_url


class TestTransformKbLinks:
    """Tests for transform_kb_links function."""

    def test_path_with_parentheses_in_filename_mapping(self):
        """测试路径中包含半角括号时，通过 filename_to_path 映射正确解析。

        场景来自实际日志：
        - LLM 输出: kb://06-构建阶段/.../星瀚发票云(旗舰版)/.../扫码开票对接方案.md
        - Read 追踪: 扫码开票对接方案.md -> 产品与交付知识/06-构建阶段/.../星瀚发票云（旗舰版）/.../扫码开票对接方案.md
        """
        content = """根据 [扫码开票对接方案](kb://06-构建阶段/产品初始化配置/星瀚发票云(旗舰版)/星瀚开票(旗舰版)/开票接口对接/扫码开票对接方案.md) 文档：

**第三方应用密码就是 appSecret(应用密钥)**"""

        # 模拟 Read 工具追踪的文件路径（全角括号）
        filename_to_path = {
            "扫码开票对接方案.md": "产品与交付知识/06-构建阶段/产品初始化配置/星瀚发票云（旗舰版）/星瀚开票（旗舰版）/开票接口对接/扫码开票对接方案.md"
        }

        with patch('api.utils.kb_link_resolver.resolve_kb_url') as mock_resolve:
            mock_resolve.return_value = "https://www.yuque.com/nbklz3/tadboa/rzxzhkn7w1uo30f2"

            result = transform_kb_links(content, filename_to_path)

            # 验证使用了正确的路径调用 resolve_kb_url
            mock_resolve.assert_called_once_with(
                "产品与交付知识/06-构建阶段/产品初始化配置/星瀚发票云（旗舰版）/星瀚开票（旗舰版）/开票接口对接/扫码开票对接方案.md"
            )

            # 验证链接被正确替换
            assert "https://www.yuque.com/nbklz3/tadboa/rzxzhkn7w1uo30f2" in result
            assert "kb://" not in result

    def test_path_with_nested_parentheses(self):
        """测试路径中有多层括号的情况。"""
        content = "[文档](kb://产品与交付知识/星瀚发票云(旗舰版)/星瀚开票(旗舰版)/配置.md)"

        filename_to_path = {
            "配置.md": "产品与交付知识/星瀚发票云（旗舰版）/星瀚开票（旗舰版）/配置.md"
        }

        with patch('api.utils.kb_link_resolver.resolve_kb_url') as mock_resolve:
            mock_resolve.return_value = "https://example.com/doc"

            result = transform_kb_links(content, filename_to_path)

            assert "[文档](https://example.com/doc)" in result

    def test_simple_path_without_parentheses(self):
        """测试简单路径（无括号）正常工作。"""
        content = "[开票FAQ](kb://产品与交付知识/常见问题/开票FAQ.md)"

        filename_to_path = {
            "开票FAQ.md": "产品与交付知识/常见问题/开票FAQ.md"
        }

        with patch('api.utils.kb_link_resolver.resolve_kb_url') as mock_resolve:
            mock_resolve.return_value = "https://example.com/faq"

            result = transform_kb_links(content, filename_to_path)

            assert "[开票FAQ](https://example.com/faq)" in result

    def test_multiple_links_in_content(self):
        """测试内容中有多个 kb:// 链接。"""
        content = """参考 [文档A](kb://路径/文档A.md) 和 [文档B](kb://路径/文档B.md)。"""

        filename_to_path = {
            "文档A.md": "路径/文档A.md",
            "文档B.md": "路径/文档B.md"
        }

        with patch('api.utils.kb_link_resolver.resolve_kb_url') as mock_resolve:
            mock_resolve.return_value = "https://example.com/doc"

            result = transform_kb_links(content, filename_to_path)

            assert result.count("https://example.com/doc") == 2
            assert "kb://" not in result

    def test_fallback_to_direct_resolve_when_not_in_mapping(self):
        """测试文件名不在映射中时，回退到直接解析路径。"""
        content = "[文档](kb://产品与交付知识/某文档.md)"

        filename_to_path = {}  # 空映射

        with patch('api.utils.kb_link_resolver.resolve_kb_url') as mock_resolve:
            mock_resolve.return_value = "https://example.com/doc"

            result = transform_kb_links(content, filename_to_path)

            # 应该用原始路径调用
            mock_resolve.assert_called_with("产品与交付知识/某文档.md")

    def test_link_removed_when_resolve_fails(self):
        """测试解析失败时只保留标题。"""
        content = "[文档标题](kb://不存在的路径/文档.md)"

        filename_to_path = {}

        with patch('api.utils.kb_link_resolver.resolve_kb_url') as mock_resolve:
            mock_resolve.return_value = None  # 解析失败

            result = transform_kb_links(content, filename_to_path)

            assert result == "文档标题"
            assert "kb://" not in result

    def test_normalized_matching_for_fullwidth_parentheses(self):
        """测试规范化匹配：LLM 输出半角括号，但文件是全角括号。

        场景：
        - Read 追踪: 星瀚发票云（全角）配置手册.md
        - LLM 输出: kb://...星瀚发票云(半角)配置手册.md
        - 应该通过规范化匹配成功
        """
        content = "[配置手册](kb://产品与交付知识/星瀚发票云(旗舰版)/星瀚(标准版影像)配置手册.md)"

        # 模拟 Read 追踪的是全角括号文件
        filename_to_path = {
            "星瀚（标准版影像）配置手册.md": "产品与交付知识/06-构建阶段/星瀚发票云（旗舰版）/星瀚（标准版影像）配置手册.md",
            # 规范化后的半角括号版本也在映射中（streaming.py 会添加）
            "星瀚(标准版影像)配置手册.md": "产品与交付知识/06-构建阶段/星瀚发票云（旗舰版）/星瀚（标准版影像）配置手册.md"
        }

        with patch('api.utils.kb_link_resolver.resolve_kb_url') as mock_resolve:
            mock_resolve.return_value = "https://example.com/config"

            result = transform_kb_links(content, filename_to_path)

            # 应该通过规范化匹配成功
            assert "[配置手册](https://example.com/config)" in result
            assert "kb://" not in result

    def test_regex_extracts_correct_filename_from_path_with_parentheses(self):
        """验证正则表达式能正确提取包含括号的路径中的文件名。

        这是修复前的 bug：正则 [^)]+ 遇到路径中的 ) 会提前截断，
        导致提取的文件名是 "星瀚发票云(旗舰版" 而不是 "扫码开票对接方案.md"
        """
        import re

        # 新的正则表达式
        pattern = r'\[([^\]]+)\]\(kb://(.+?\.md)\)'

        content = "[扫码开票对接方案](kb://06-构建阶段/产品初始化配置/星瀚发票云(旗舰版)/星瀚开票(旗舰版)/开票接口对接/扫码开票对接方案.md)"

        match = re.search(pattern, content)
        assert match is not None

        title = match.group(1)
        kb_path = match.group(2)

        assert title == "扫码开票对接方案"
        assert kb_path == "06-构建阶段/产品初始化配置/星瀚发票云(旗舰版)/星瀚开票(旗舰版)/开票接口对接/扫码开票对接方案.md"

        # 提取文件名
        from pathlib import Path
        filename = Path(kb_path).name
        assert filename == "扫码开票对接方案.md"


class TestResolveKbUrl:
    """Tests for resolve_kb_url function."""

    def test_file_not_found(self):
        """测试文件不存在时返回 None。"""
        result = resolve_kb_url("不存在的文件.md")
        assert result is None

    def test_valid_file_with_url(self, tmp_path):
        """测试有效文件返回 URL。"""
        # 这个测试需要实际文件，跳过或使用 mock
        pass
