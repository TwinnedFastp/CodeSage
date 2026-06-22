"""
函数调用审计数据模型

表与职责：
- function_call_audit  工具/函数调用审计日志（命名、入参、结果、状态、耗时）

设计要点：
- user_id 在用户删除时置 NULL（ondelete=SET NULL），保留审计痕迹
- status 枚举：success / failed / denied / timeout
- params_json / result_json 以 JSONB 存储，兼顾灵活查询
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from backend.models.base import Base


class FunctionCallAudit(Base):
    """
    函数调用审计：记录每次工具/函数调用的入参、结果、状态与耗时，便于追溯与排查。
    """
    __tablename__ = "function_call_audit"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    function_name = Column(String(128), nullable=False)
    params_json = Column(JSONB, nullable=False, default=dict, server_default="{}")
    result_json = Column(JSONB, nullable=True)
    status = Column(String(16), nullable=False, default="success", server_default="success")
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_function_call_audit_user_created", "user_id", "created_at"),
    )
