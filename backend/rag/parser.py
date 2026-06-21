"""
轻量级文档解析器。

只做最基础的清理工作（去除多余空行、标准化格式），
复杂的分块/实体抽取/向量化全部交给 LightRAG ainsert 处理。
"""

import re


def parse_markdown(text: str) -> str:
    """
    清理 Markdown 文本：去除多余空行，保留结构。

    不做语义解析 —— LightRAG 的 insert 会自行处理分块和实体抽取。
    """
    # 去除首尾空白
    text = text.strip()
    # 将 3 个以上连续空行压缩为 2 个（段落间保留一个空行）
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 去除行尾空白
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    return text


def extract_text_from_content(content: str, filename: str) -> str:
    """
    根据文件扩展名分发到对应解析器。

    目前支持 .md / .txt，后续可扩展 .pdf / .docx 等。
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("md", "markdown"):
        return parse_markdown(content)
    elif ext == "txt":
        return content.strip()
    else:
        # 未知类型当作纯文本处理
        return content.strip()
