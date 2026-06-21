"""
LLM 会话存储接口：会话 / 消息 / 偏好 / 事实记忆 / 任务 的 CRUD
所有接口均需登录（依赖 get_current_user），并按 current_user.id 隔离数据。
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.conversation import (
    FactCreate, FactOut, FactUpdate, MessageCreate, MessageOut,
    PreferenceOut, PreferenceUpdate, SessionCreate, SessionOut, SessionUpdate,
    TaskCreate, TaskOut, TaskUpdate,
)
from backend.services import conversation_service

router = APIRouter()


def _err(exc: conversation_service.ConversationError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"message": exc.message})


# ------------------------------------------------------------------
# 会话
# ------------------------------------------------------------------
@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.create_session(db, user.id, payload.title)
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    limit: int = Query(50, le=200), offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    return await conversation_service.list_sessions(db, user.id, limit, offset)


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.get_session(db, user.id, session_id)
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.patch("/sessions/{session_id}", response_model=SessionOut)
async def update_session(
    session_id: UUID, payload: SessionUpdate,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.update_session(
            db, user.id, session_id, payload.title, payload.summary
        )
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        await conversation_service.delete_session(db, user.id, session_id)
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.post("/sessions/{session_id}/generate-title", response_model=SessionOut)
async def generate_session_title(
    session_id: UUID,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    """根据 AI 对话内容自动生成会话标题。"""
    try:
        return await conversation_service.generate_title(db, user.id, session_id)
    except conversation_service.ConversationError as exc:
        return _err(exc)
    except Exception as exc:
        return JSONResponse(status_code=500, content={"message": f"生成标题失败：{str(exc)}"})


# ------------------------------------------------------------------
# 原始聊天记录
# ------------------------------------------------------------------
@router.post("/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def add_message(
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.add_message(
            db, user.id, payload.session_id, payload.role, payload.content
        )
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: UUID,
    limit: int = Query(100, le=500), offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.list_messages(db, user.id, session_id, limit, offset)
    except conversation_service.ConversationError as exc:
        return _err(exc)


# ------------------------------------------------------------------
# 用户长期偏好
# ------------------------------------------------------------------
@router.put("/preferences", response_model=PreferenceOut)
async def update_preferences(
    payload: PreferenceUpdate,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.upsert_preferences(db, user.id, payload.preferences)
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.get("/preferences", response_model=PreferenceOut)
async def get_preferences(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    pref = await conversation_service.get_preferences(db, user.id)
    if pref is None:
        return PreferenceOut(user_id=user.id, preferences={}, updated_at=None)  # type: ignore[arg-type]
    return pref


# ------------------------------------------------------------------
# 重要事实记忆
# ------------------------------------------------------------------
@router.post("/facts", response_model=FactOut, status_code=status.HTTP_201_CREATED)
async def upsert_fact(
    payload: FactCreate,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.upsert_fact(
            db, user.id, payload.fact_key, payload.fact_value, payload.fact_category
        )
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.get("/facts", response_model=list[FactOut])
async def list_facts(
    category: Optional[str] = None,
    limit: int = Query(100, le=500), offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    return await conversation_service.list_facts(db, user.id, category, limit, offset)


@router.delete("/facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact(
    fact_id: int,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        await conversation_service.delete_fact(db, user.id, fact_id)
    except conversation_service.ConversationError as exc:
        return _err(exc)


# ------------------------------------------------------------------
# 任务状态
# ------------------------------------------------------------------
@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.create_task(
            db, user.id, payload.title, payload.description,
            payload.session_id, payload.due_date, payload.status,
        )
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    status: Optional[str] = None,
    limit: int = Query(100, le=500), offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    return await conversation_service.list_tasks(db, user.id, status, limit, offset)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int, payload: TaskUpdate,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await conversation_service.update_task(
            db, user.id, task_id, payload.title, payload.description, payload.status, payload.due_date,
        )
    except conversation_service.ConversationError as exc:
        return _err(exc)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        await conversation_service.delete_task(db, user.id, task_id)
    except conversation_service.ConversationError as exc:
        return _err(exc)
