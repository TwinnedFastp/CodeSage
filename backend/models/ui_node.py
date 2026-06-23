"""
UI 卡片节点版本化数据模型

表与职责：
- ui_node           卡片节点（父子树结构，关联会话与用户）
- ui_node_version   节点版本（组件协议 JSONB + 可选 HTML 快照，支持多版本回溯）
- ui_node_relation  节点间关系（引用 / 展开 / 引用等三元组）

设计要点：
- current_version_id 不建外键，避免与 ui_node_version 形成循环 DDL，由服务层维护一致性
- content_json 存储组件协议 ComponentProtocol，分片/渲染由前端解析
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from backend.models.base import Base


class UiNode(Base):
    """
    卡片节点：对话中生成的 UI 单元，支持父子树与多版本。
    """
    __tablename__ = "ui_node"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("ui_node.id", ondelete="SET NULL"), nullable=True, index=True)
    current_version_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    node_type = Column(String(64), nullable=False, default="root", server_default="root")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_ui_node_user_conv", "user_id", "conversation_id"),
    )


class UiNodeVersion(Base):
    """
    节点版本：每次生成/重生成/展开均写入新版本，支持回溯与切换。
    """
    __tablename__ = "ui_node_version"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    node_id = Column(UUID(as_uuid=True), ForeignKey("ui_node.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False)
    content_json = Column(JSONB, nullable=False)
    html_snapshot = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="llm", server_default="llm")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("node_id", "version_no", name="uq_ui_node_version_node_no"),
        Index("ix_ui_node_version_node_created", "node_id", "created_at"),
    )


class UiNodeRelation(Base):
    """
    节点间关系：引用 / 展开 / 引用等有向三元组，构建卡片关联图。
    """
    __tablename__ = "ui_node_relation"

    id = Column(BigInteger, primary_key=True, index=True)
    from_node_id = Column(UUID(as_uuid=True), ForeignKey("ui_node.id", ondelete="CASCADE"), nullable=False, index=True)
    to_node_id = Column(UUID(as_uuid=True), ForeignKey("ui_node.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("from_node_id", "to_node_id", "relation_type", name="uq_ui_node_relation_triple"),
    )
