import re
from ubbrand import replace_dice_tags


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
    text = re.sub(r"\[collapse=.*?\](.*?)\[/collapse\]", r"\1", text, flags=re.DOTALL)
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
        quoted = "\n".join("> " + line.strip() for line in lines if line.strip())
        return quoted

    return re.sub(r"\[quote\](.*?)\[/quote\]", replace_quote, text, flags=re.DOTALL)
