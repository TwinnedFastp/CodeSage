"""
模型统一导出：导入所有模型以确保 Base.metadata 注册完整。
"""
from backend.models.base import Base
from backend.models.user import User, LoginLog
from backend.models.conversation import (
    ChatSession,
    ChatMessage,
    UserPreference,
    UserFact,
    UserTask,
)

__all__ = [
    "Base",
    "User",
    "LoginLog",
    "ChatSession",
    "ChatMessage",
    "UserPreference",
    "UserFact",
    "UserTask",
]
