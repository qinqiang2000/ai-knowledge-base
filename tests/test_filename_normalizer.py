"""Tests for filename_normalizer module."""

from api.utils.filename_normalizer import normalize_filename


class TestNormalizeFilename:
    """Tests for normalize_filename function."""

    def test_fullwidth_parentheses_to_halfwidth(self):
        """测试全角括号转半角括号。"""
        assert normalize_filename("星瀚发票云（旗舰版）.md") == "星瀚发票云(旗舰版).md"
        assert normalize_filename("配置（新）手册.md") == "配置(新)手册.md"

    def test_fullwidth_space_to_halfwidth(self):
        """测试全角空格转半角空格。"""
        assert normalize_filename("配置　手册.md") == "配置 手册.md"
        assert normalize_filename("文档　说明　书.md") == "文档 说明 书.md"

    def test_mixed_fullwidth_and_halfwidth(self):
        """测试混合全角半角字符。"""
        assert normalize_filename("星瀚（旗舰版）　配置(手册).md") == "星瀚(旗舰版) 配置(手册).md"

    def test_no_change_for_normal_filename(self):
        """测试普通文件名不变。"""
        assert normalize_filename("normal_file.md") == "normal_file.md"
        assert normalize_filename("文档.md") == "文档.md"

    def test_empty_and_none(self):
        """测试空字符串和 None。"""
        assert normalize_filename("") == ""
        assert normalize_filename(None) == None

    def test_only_converts_specified_characters(self):
        """测试只转换指定字符，其他字符不变。"""
        # 全角数字和英文字母不应该被转换（除非添加规则）
        filename = "文档１２３ＡＢＣ.md"
        # 当前规则不转换这些，所以应该不变
        assert normalize_filename(filename) == filename

    def test_real_world_case_from_logs(self):
        """测试来自实际日志的案例。"""
        # 来自 app.log 第61行的文件名
        original = "星瀚（标准版影像）配置手册.md"
        expected = "星瀚(标准版影像)配置手册.md"
        assert normalize_filename(original) == expected
