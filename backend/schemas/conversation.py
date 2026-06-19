"""
LLM 会话存储相关 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


# ------------------------------------------------------------------
# 会话
# ------------------------------------------------------------------
class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None


class SessionOut(BaseModel):
    id: UUID
    user_id: int
    title: Optional[str]
    summary: Optional[str]
    summary_generated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# 消息
# ------------------------------------------------------------------
class MessageCreate(BaseModel):
    session_id: UUID
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class MessageOut(BaseModel):
    id: int
    message_id: UUID
    session_id: UUID
    user_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# 用户偏好
# ------------------------------------------------------------------
class PreferenceUpdate(BaseModel):
    """整体或部分合并更新；preferences 为 JSON 对象"""
    preferences: dict[str, Any]


class PreferenceOut(BaseModel):
    user_id: int
    preferences: dict[str, Any]
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# 重要事实
# ------------------------------------------------------------------
class FactCreate(BaseModel):
    fact_key: str
    fact_value: str
    fact_category: Optional[str] = None


class FactUpdate(BaseModel):
    fact_value: Optional[str] = None
    fact_category: Optional[str] = None


class FactOut(BaseModel):
    id: int
    user_id: int
    fact_key: str
    fact_value: str
    fact_category: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# 任务
# ------------------------------------------------------------------
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    session_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    status: str = Field("pending", pattern="^(pending|in_progress|completed|cancelled)$")


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    due_date: Optional[datetime] = None


class TaskOut(BaseModel):
    id: int
    user_id: int
    session_id: Optional[UUID]
    title: str
    description: Optional[str]
    status: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
