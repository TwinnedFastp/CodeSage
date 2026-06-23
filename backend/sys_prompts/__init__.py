"""
AI 提示词集中管理模块。

所有 system prompt / instruction 均以 .md 文件存储在本包目录下，
运行时读取为字符串导出，方便统一管理和迭代。

文件清单：
├── chat_system.md              # 主聊天系统提示词
├── title_generator.md          # 会话标题生成提示词
├── component_protocol.md       # 组件协议（UI 生成）提示词
├── regenerate_instruction.md   # "再思考"默认指令
└── expand_instruction.md       # "展开"默认指令

使用方式：
    from backend.sys_prompts import (
        CHAT_SYSTEM_PROMPT,          # chat.py → _build_system_prompt()
        TITLE_GENERATOR_PROMPT,      # conversation_service.py → generate_title()
        COMPONENT_PROTOCOL_PROMPT,   # component_service.py → generate_component_protocol()
        REGENERATE_INSTRUCTION,      # node_service.py → regenerate_node()
        EXPAND_INSTRUCTION,          # node_service.py → expand_node()
    )
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def _load(name: str) -> str:
    """读取提示词 .md 文件内容。"""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


# ============================================================================
# 提示词常量定义
# ============================================================================

# CodeSage 主系统提示词（聊天接口使用）
# 调用: backend/api/v1/endpoints/chat.py → _build_system_prompt() → chat()
CHAT_SYSTEM_PROMPT: str = _load("chat_system.md")

# 标题生成器提示词（会话服务使用）
# 调用: backend/services/conversation_service.py → generate_title()
TITLE_GENERATOR_PROMPT: str = _load("title_generator.md")

# 组件协议生成器提示词（界面生成接口使用）
# 调用: backend/services/component_service.py → generate_component_protocol()
#      backend/services/component_service.py → stream_component_protocol_raw()
COMPONENT_PROTOCOL_PROMPT: str = _load("component_protocol.md")

# "再思考"按钮默认指令（节点服务使用）
# 调用: backend/services/node_service.py → regenerate_node()
REGENERATE_INSTRUCTION: str = _load("regenerate_instruction.md")

# "展开"按钮默认指令（节点服务使用）
# 调用: backend/services/node_service.py → expand_node()
EXPAND_INSTRUCTION: str = _load("expand_instruction.md")


__all__ = [
    "CHAT_SYSTEM_PROMPT",
    "TITLE_GENERATOR_PROMPT",
    "COMPONENT_PROTOCOL_PROMPT",
    "REGENERATE_INSTRUCTION",
    "EXPAND_INSTRUCTION",
]
