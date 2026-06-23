"""
文档内容提取工具

支持从 PDF、DOCX、TXT、MD 文件中提取文本内容。
前端将文件转为 base64 后传给后端，后端解码并提取文本。
"""
import base64
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_base64(base64_data: str, filename: str) -> str:
    """
    从 base64 编码的文件中提取文本内容。

    Args:
        base64_data: base64 编码的文件数据（可带 data URL 前缀）
        filename: 文件名（用于判断文件类型）

    Returns:
        提取的文本内容
    """
    if "," in base64_data:
        base64_data = base64_data.split(",", 1)[1]

    file_bytes = base64.b64decode(base64_data)
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_from_pdf(file_bytes)
    elif ext == ".docx":
        return _extract_from_docx(file_bytes)
    elif ext in {".txt", ".md", ".markdown"}:
        return _extract_from_text(file_bytes)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def _extract_from_pdf(file_bytes: bytes) -> str:
    """从 PDF 文件提取文本"""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as exc:
        logger.exception("PDF 提取失败")
        raise ValueError(f"PDF 文件解析失败: {exc}") from exc


def _extract_from_docx(file_bytes: bytes) -> str:
    """从 DOCX 文件提取文本"""
    try:
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        return "\n\n".join(text_parts)
    except Exception as exc:
        logger.exception("DOCX 提取失败")
        raise ValueError(f"DOCX 文件解析失败: {exc}") from exc


def _extract_from_text(file_bytes: bytes) -> str:
    """从纯文本文件提取内容"""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("gbk", errors="ignore")
