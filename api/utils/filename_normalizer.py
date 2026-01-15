"""文件名规范化工具 - 提高 kb:// 链接匹配稳定性."""


def normalize_filename(filename: str) -> str:
    """规范化文件名，统一全角/半角字符。

    主要用于处理 LLM 输出不一致的问题（如全角括号变半角）。

    规范化规则：
    - 全角括号 （） → 半角括号 ()
    - 全角空格 　 → 半角空格
    - 保持其他字符不变

    Args:
        filename: 原始文件名

    Returns:
        规范化后的文件名

    Examples:
        >>> normalize_filename("星瀚发票云（旗舰版）.md")
        "星瀚发票云(旗舰版).md"
        >>> normalize_filename("配置　手册.md")
        "配置 手册.md"
    """
    if not filename:
        return filename

    # 全角括号 → 半角括号
    normalized = filename.replace('（', '(').replace('）', ')')

    # 全角空格 → 半角空格
    normalized = normalized.replace('　', ' ')

    # 可以根据需要添加更多规范化规则
    # 例如：全角数字、英文字母等

    return normalized
