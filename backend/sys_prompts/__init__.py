"""
AI 提示词集中管理模块。

所有 system prompt 均以 .md 文件存储在本包目录下，
运行时读取为字符串导出，方便统一管理和迭代。

使用方式：
    from backend.sys_prompts import CHAT_SYSTEM_PROMPT, TITLE_GENERATOR_PROMPT
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def _load(name: str) -> str:
    """读取提示词 .md 文件内容。"""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


# CodeSage 主系统提示词（聊天接口使用）
CHAT_SYSTEM_PROMPT: str = _load("chat_system.md")

# 标题生成器提示词（会话服务使用）
TITLE_GENERATOR_PROMPT: str = _load("title_generator.md")

__all__ = ["CHAT_SYSTEM_PROMPT", "TITLE_GENERATOR_PROMPT"]
