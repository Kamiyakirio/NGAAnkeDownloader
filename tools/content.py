import re
import json

from tools.ubbrand import replace_dice_tags


def nga_content_convert_to_markdown(
    text, authorId=None, tId=None, pId=None, seedOffset=0
):
    # 替换 [quote] 标签（支持嵌套）
    text = process_quote_blocks(text)
    # 替换加粗
    text = re.sub(r"\[b\](.*?)\[/b\]", r"**\1**", text, flags=re.DOTALL)
    # 替换斜体
    text = re.sub(r"\[i\](.*?)\[/i\]", r"*\1*", text, flags=re.DOTALL)
    # 替换删除线
    text = re.sub(r"\[del\](.*?)\[/del\]", r"~~\1~~", text, flags=re.DOTALL)
    # 删除图片
    text = re.sub(r"\[img\].*?\[/img\]", "", text, flags=re.DOTALL)
    # collapse：保留内容
    text = re.sub(r"\[collapse=.*?\](.*?)\[/collapse\]",
                  r"\1", text, flags=re.DOTALL)
    # 删除颜色标签
    text = re.sub(r"\[/?color=.*?\]", "", text)
    # 删除表情
    text = re.sub(r"\[s:[^\]]+\]", "", text)
    # 替换骰子标签（最后）
    text = replace_dice_tags(text, authorId, tId, pId, seedOffset)
    # 删除其他未知标签（保留内容）
    text = re.sub(r"\[/?\w+(=[^\]]+)?\]", "", text)
    return text.strip()


def process_quote_blocks(text):
    # 支持嵌套 quote 的递归处理
    def replace_quote(match):
        quote_content = match.group(1).strip()
        # 递归处理内部 quote
        quote_content = re.sub(
            r"\[quote\](.*?)\[/quote\]", replace_quote, quote_content, flags=re.DOTALL
        )
        # 每行加上 >
        lines = quote_content.splitlines()
        quoted = "\n".join("> " + line.strip()
                           for line in lines if line.strip())
        return quoted

    return re.sub(r"\[quote\](.*?)\[/quote\]", replace_quote, text, flags=re.DOTALL)


def extract_user_info(html_content: str) -> dict:
    """
    从HTML内容中提取用户信息JSON

    Args:
        html_content: 包含用户信息的HTML内容

    Returns:
        提取出的用户信息字典
    """

    # 使用正则表达式匹配注释之间的内容
    pattern = r'//userinfostart\r\n(.*?)\r\n//userinfoend'
    match = re.search(pattern, html_content, re.DOTALL)

    if not match:
        raise ValueError("未找到用户信息数据")

    # 提取JSON字符串
    json_str = match.group(1)

    # 解析JSON
    try:
        # 移除commonui.userInfo.setAll(和最后的)包装
        json_str = json_str.replace(
            'commonui.userInfo.setAll(', '').rstrip(' )')
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {str(e)}")

# 使用示例：
# html_content = "你的HTML内容"
# user_info = extract_user_info(html_content)
# print(user_info)
