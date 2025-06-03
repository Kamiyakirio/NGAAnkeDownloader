import re
import json

from tools.ubbrand import replace_dice_tags


def nga_content_convert_to_markdown(
    text, authorId=None, tId=None, pId=None, seedOffset=0
):
    # 先处理表格
    text = process_table_blocks(text)
    # 处理嵌套quote
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


def process_table_blocks(text):
    # 递归处理所有table标签
    def replace_table(match):
        table_content = match.group(1)
        # 解析table中的tr
        rows = re.findall(r"\[tr\](.*?)\[/tr\]", table_content, flags=re.DOTALL)
        if not rows:
            return ""

        # 解析每行中的td，提取纯文本（去除align, b标签等）
        table_rows = []
        for row in rows:
            # 匹配td内容
            cols = re.findall(r"\[td.*?\](.*?)\[/td\]", row, flags=re.DOTALL)
            cleaned_cols = []
            for col in cols:
                # 去除多余标签和换行
                col_text = col
                # 删除对齐标签等 [align=center] [b]等
                col_text = re.sub(
                    r"\[/?(align|b|size|color|url|font|/font|/size|/color).*?\]",
                    "",
                    col_text,
                )

                if "纷乱箭" in col_text:
                    pass

                # 替换换行符和 <br/> 为换行符
                # col_text = re.sub(r"<br\s*/?>", "\n", col_text)
                # 去除剩余的标签（[]标签）
                col_text = re.sub(r"\[/?\w+(=[^\]]+)?\]", "", col_text)
                # 多余空白转单空格
                col_text = re.sub(r"[ \t\r\f\v]+", " ", col_text)
                # 去除首尾空白和换行符两端空白
                col_text = col_text.strip()
                # 把换行转成空格（Markdown表格单元格内不支持换行）
                col_text = col_text.replace("\n", "<br/>")
                cleaned_cols.append(col_text)
            table_rows.append(cleaned_cols)

        # 构建Markdown表格
        # 默认第一行为表头
        header = table_rows[0]
        # 制作分隔行，数量和表头列数对应
        separator = ["---"] * len(header)

        md_lines = []
        # 拼接表头
        md_lines.append("| " + " | ".join(header) + " |")
        md_lines.append("| " + " | ".join(separator) + " |")
        # 拼接剩余行
        for row in table_rows[1:]:
            # 保证列数和表头相同，不足补空，多余截断
            row_fixed = row[: len(header)] + [""] * max(0, len(header) - len(row))
            md_lines.append("| " + " | ".join(row_fixed) + " |")

        return "\n".join(md_lines) + "\n\n"

    # 递归替换所有table
    while True:
        new_text, count = re.subn(
            r"\[table\](.*?)\[/table\]", replace_table, text, flags=re.DOTALL
        )
        if count == 0:
            break
        text = new_text
    return text


def extract_user_info(html_content: str) -> dict:
    """
    从HTML内容中提取用户信息JSON

    Args:
        html_content: 包含用户信息的HTML内容

    Returns:
        提取出的用户信息字典
    """

    # 使用正则表达式匹配注释之间的内容
    pattern = r"//userinfostart\r\n(.*?)\r\n//userinfoend"
    match = re.search(pattern, html_content, re.DOTALL)

    if not match:
        raise ValueError("未找到用户信息数据")

    # 提取JSON字符串
    json_str = match.group(1)

    # 解析JSON
    try:
        # 移除commonui.userInfo.setAll(和最后的)包装
        json_str = json_str.replace("commonui.userInfo.setAll(", "").rstrip(" )")
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {str(e)}")


# 使用示例：
# html_content = "你的HTML内容"
# user_info = extract_user_info(html_content)
# print(user_info)
