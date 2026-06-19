"""
LLM 会话存储相关数据模型（第一版：纯 PostgreSQL，暂不引入向量库）

表与职责（对应需求第二部分）：
- chat_sessions       会话（含自动生成的核心内容摘要）        -> 需求2 会话摘要
- chat_messages       原始聊天记录（每轮对话原文/角色/时间/消息ID）-> 需求1 原始聊天记录
- user_preferences    用户长期偏好（多轮对话持续体现，JSONB 动态更新）-> 需求3 用户长期偏好
- user_facts          重要事实记忆（关键个人信息/需求，强关联 user_id） -> 需求4 重要事实记忆
- user_tasks          任务状态（会话衍生待办/进度/截止时间，支持流转）  -> 需求5 任务状态

数据隔离：所有表均带 user_id 索引，查询时强制按 user_id 过滤。
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from backend.models.base import Base


class ChatSession(Base):
    """
    会话表：一场 LLM 对话的容器，关联一批原始消息，并存储自动摘要。
    """
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(256), nullable=True)
    summary = Column(Text, nullable=True)
    summary_generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_chat_sessions_user_created", "user_id", "created_at"),
    )


class ChatMessage(Base):
    """
    原始聊天记录：用户与 LLM 的每一轮对话原文。
    - message_id 为业务唯一消息 ID（UUID），便于幂等写入与外部引用
    - user_id 冗余存储，避免跨表 JOIN 即可完成数据隔离过滤
    """
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, index=True)
    message_id = Column(UUID(as_uuid=True), unique=True, nullable=False, server_default=func.gen_random_uuid())
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(16), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
        Index("ix_chat_messages_user_created", "user_id", "created_at"),
    )


class UserPreference(Base):
    """
    用户长期偏好：JSONB 动态存储，整体 upsert，按 user_id 唯一。
    """
    __tablename__ = "user_preferences"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    preferences = Column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserFact(Base):
    """
    重要事实记忆：用户提及的关键个人信息/需求事实。
    - fact_value 敏感，经 utils.crypto 加密后存储
    - fact_category 用于分类检索（如 profile / requirement / preference）
    """
    __tablename__ = "user_facts"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fact_key = Column(String(128), nullable=False)
    fact_value = Column(Text, nullable=False)  # 加密存储
    fact_category = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "fact_key", name="uq_user_facts_user_key"),
        Index("ix_user_facts_user_category", "user_id", "fact_category"),
    )


class UserTask(Base):
    """
    任务状态：会话中衍生的待办任务，支持状态流转。
    状态机：pending -> in_progress -> completed | cancelled
    """
    __tablename__ = "user_tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="pending", server_default="pending")
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_user_tasks_user_status", "user_id", "status"),
        Index("ix_user_tasks_user_due", "user_id", "due_date"),
    )
