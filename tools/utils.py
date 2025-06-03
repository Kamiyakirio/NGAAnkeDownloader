import re
import os


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    清理文件名中的非法字符。

    参数：
    - filename: 原始文件名字符串
    - replacement: 用于替代非法字符的字符，默认是 '_'

    返回：
    - 清理后的合法文件名字符串
    """
    # Windows 不允许的字符
    invalid_chars = r'[<>:"/\\|?*]'

    # 去除 Windows 保留名称（如CON, PRN 等）只在无扩展名时处理
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }

    # 清除非法字符
    cleaned = re.sub(invalid_chars, replacement, filename)

    # 如果有扩展名，提取主名判断保留名
    base_name = cleaned.split(".")[0].upper()
    if base_name in reserved_names:
        cleaned = "_" + cleaned

    return cleaned


def check_folders():
    if not os.path.exists(os.path.join(os.getcwd(), "data")):
        os.makedirs(os.path.join(os.getcwd(), "data"))
