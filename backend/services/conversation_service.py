"""
LLM 会话存储服务

覆盖需求第二部分五类核心数据，全部基于 PostgreSQL（第一版）：
1. 原始聊天记录  -> ChatMessage
2. 会话摘要      -> ChatSession.summary
3. 用户长期偏好  -> UserPreference (JSONB)
4. 重要事实记忆  -> UserFact (fact_value 加密存储)
5. 任务状态      -> UserTask

通用约束：
- 所有查询强制按 user_id 过滤，保证多用户数据隔离
- 所有写操作在事务中执行，异常捕获并回滚
- 敏感字段（fact_value）经 utils.crypto 加密后入库，读取时解密
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.conversation import (
    ChatMessage,
    ChatSession,
    UserFact,
    UserPreference,
    UserTask,
)
from backend.sys_prompts import TITLE_GENERATOR_PROMPT
from backend.utils.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)


class ConversationError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


# ==================================================================
# 会话
# ==================================================================
async def create_session(db: AsyncSession, user_id: int, title: Optional[str] = None) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("创建会话失败 user_id=%s", user_id)
        raise ConversationError("创建会话失败", status=500)
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, user_id: int, session_id: UUID) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ConversationError("会话不存在或无权访问", status=404)
    return session


async def list_sessions(db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0) -> list[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def update_session(
    db: AsyncSession, user_id: int, session_id: UUID,
    title: Optional[str] = None, summary: Optional[str] = None,
) -> ChatSession:
    session = await get_session(db, user_id, session_id)
    if title is not None:
        session.title = title
    if summary is not None:
        session.summary = summary
        session.summary_generated_at = datetime.now(timezone.utc)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("更新会话失败", status=500)
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, user_id: int, session_id: UUID) -> None:
    session = await get_session(db, user_id, session_id)
    try:
        await db.delete(session)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("删除会话失败", status=500)


async def generate_title(
    db: AsyncSession, user_id: int, session_id: UUID,
    provider_config: dict | None = None,
) -> ChatSession:
    """
    根据会话前几条消息调用 LLM 生成简短标题，并更新到数据库。

    provider_config: 用户的供应商配置（含 api_key / base_url / model）。
    若为 None，则从 DB 解析用户生效配置（ai_providers 表）。

    失败兜底策略：LLM 调用异常 / 返回空字符串时，使用第一条用户消息的前
    15 个字符作为标题，避免标题永远停留在"新会话"；该兜底不会抛异常。
    """
    from openai import AsyncOpenAI

    # 未传入配置时，从 DB 解析用户生效配置
    if provider_config is None:
        from backend.services.provider_service import resolve_provider_config
        provider_config = await resolve_provider_config(db, user_id)
        if not provider_config:
            raise ConversationError("未配置 AI 供应商，无法生成标题", status=400)

    msgs = await list_messages(db, user_id, session_id, limit=4, offset=0)
    if len(msgs) < 2:
        raise ConversationError("消息不足，无法生成标题", status=400)

    conversation_text = "\n".join(
        f"{'用户' if m.role == 'user' else 'AI'}：{m.content[:200]}"
        for m in msgs[:4]
    )

    # 先计算兜底标题：LLM 异常或空返回时使用，避免标题永久停在"新会话"
    fallback_title = _extract_fallback_title(msgs)
    title = fallback_title or "新会话"

    try:
        ai_client = AsyncOpenAI(
            api_key=provider_config["llm_api_key"],
            base_url=provider_config["llm_base_url"],
        )
        response = await ai_client.chat.completions.create(
            model=provider_config["llm_model"],
            messages=[
                {"role": "system", "content": TITLE_GENERATOR_PROMPT},
                {"role": "user", "content": f"请为以下对话生成一个简短标题：\n\n{conversation_text}"},
            ],
            max_tokens=30,
            temperature=0.3,
        )
        raw_title = (response.choices[0].message.content or "").strip().strip('"\'`').strip()
        if raw_title:
            # 与提示词约定的 5~15 字对齐，截断到 15 字以内
            title = raw_title[:15]
        # raw_title 为空时沿用 fallback_title
    except Exception as exc:
        # LLM 失败不抛错，沿用兜底标题，前端仍能拿到合理标题
        logger.warning(
            "LLM 生成标题失败，使用兜底标题 session_id=%s err=%s", session_id, exc,
        )

    return await update_session(db, user_id, session_id, title=title)


def _extract_fallback_title(msgs: list[ChatMessage]) -> str:
    """
    从历史消息中提取兜底标题：
    取第一条 role=user 的消息内容前 15 个字符，去除首尾空白并折叠中间换行/多空格。
    找不到用户消息（极端情况）时返回空串，由调用方继续兜底为"新会话"。
    """
    for m in msgs:
        if m.role == "user":
            text = (m.content or "").strip()
            if not text:
                continue
            # 折叠换行与多余空白为单空格，避免标题里出现换行符
            text = " ".join(text.split())
            return text[:15]
    return ""


# ==================================================================
# 原始聊天记录
# ==================================================================
async def add_message(
    db: AsyncSession, user_id: int, session_id: UUID, role: str, content: str,
) -> ChatMessage:
    # 校验会话归属
    await get_session(db, user_id, session_id)
    msg = ChatMessage(user_id=user_id, session_id=session_id, role=role, content=content)
    db.add(msg)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("写入消息失败", status=500)
    await db.refresh(msg)
    return msg


async def list_messages(
    db: AsyncSession, user_id: int, session_id: UUID, limit: int = 100, offset: int = 0,
) -> list[ChatMessage]:
    await get_session(db, user_id, session_id)  # 隔离校验
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def build_short_term_messages(
    db: AsyncSession, user_id: int, session_id, limit: int = 20
) -> list[dict]:
    """组装短期记忆：取最近 limit 条消息转为 {role, content} 字典列表。"""
    sid = UUID(session_id) if isinstance(session_id, str) else session_id
    msgs = await list_messages(db, user_id, sid, limit=limit, offset=0)
    return [
        {"role": "user" if m.role == "user" else "assistant", "content": m.content}
        for m in msgs
    ]


# ==================================================================
# 用户长期偏好（JSONB 整体 upsert + 合并）
# ==================================================================
async def upsert_preferences(db: AsyncSession, user_id: int, partial: dict[str, Any]) -> UserPreference:
    """
    部分合并更新：读取已有 preferences，浅合并 partial 后整体写回。
    使用 PostgreSQL 原生 jsonb 合并操作避免读改写竞态：
      preferences = preferences || :partial
    """
    stmt = (
        pg_insert(UserPreference)
        .values(user_id=user_id, preferences=partial)
        .on_conflict_do_update(
            index_elements=[UserPreference.user_id],
            set_={
                "preferences": UserPreference.preferences.op("||")(partial),
                "updated_at": func.now(),
            },
        )
        .returning(UserPreference)
    )
    try:
        result = await db.execute(stmt)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("更新用户偏好失败 user_id=%s", user_id)
        raise ConversationError("更新偏好失败", status=500)
    return result.scalar_one()


async def replace_preferences(db: AsyncSession, user_id: int, full: dict[str, Any]) -> UserPreference:
    """整体覆盖替换偏好。"""
    stmt = (
        pg_insert(UserPreference)
        .values(user_id=user_id, preferences=full)
        .on_conflict_do_update(
            index_elements=[UserPreference.user_id],
            set_={"preferences": full, "updated_at": func.now()},
        )
        .returning(UserPreference)
    )
    try:
        result = await db.execute(stmt)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("替换偏好失败", status=500)
    return result.scalar_one()


async def get_preferences(db: AsyncSession, user_id: int) -> Optional[UserPreference]:
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    return result.scalar_one_or_none()


# ==================================================================
# 重要事实记忆（fact_value 加密存储）
# ==================================================================
async def upsert_fact(
    db: AsyncSession, user_id: int, fact_key: str, fact_value: str,
    fact_category: Optional[str] = None,
) -> UserFact:
    """按 (user_id, fact_key) 唯一键 upsert；fact_value 加密入库。"""
    encrypted = encrypt(fact_value)
    stmt = (
        pg_insert(UserFact)
        .values(
            user_id=user_id,
            fact_key=fact_key,
            fact_value=encrypted,
            fact_category=fact_category,
        )
        .on_conflict_do_update(
            constraint="uq_user_facts_user_key",
            set_={"fact_value": encrypted, "fact_category": fact_category, "updated_at": func.now()},
        )
        .returning(UserFact)
    )
    try:
        result = await db.execute(stmt)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("写入事实记忆失败 user_id=%s key=%s", user_id, fact_key)
        raise ConversationError("写入事实记忆失败", status=500)
    fact = result.scalar_one()
    fact.fact_value = fact_value  # 回填明文供上层返回
    return fact


async def list_facts(
    db: AsyncSession, user_id: int, category: Optional[str] = None,
    limit: int = 100, offset: int = 0,
) -> list[UserFact]:
    stmt = select(UserFact).where(UserFact.user_id == user_id)
    if category:
        stmt = stmt.where(UserFact.fact_category == category)
    stmt = stmt.order_by(UserFact.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    facts = list(result.scalars().all())
    for f in facts:
        f.fact_value = decrypt(f.fact_value) or ""
    return facts


async def delete_fact(db: AsyncSession, user_id: int, fact_id: int) -> None:
    result = await db.execute(
        delete(UserFact).where(UserFact.id == fact_id, UserFact.user_id == user_id)
    )
    if result.rowcount == 0:
        raise ConversationError("事实记忆不存在或无权访问", status=404)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("删除事实记忆失败", status=500)


# ==================================================================
# 任务状态
# ==================================================================
_VALID_TASK_STATUS = {"pending", "in_progress", "completed", "cancelled"}


async def create_task(
    db: AsyncSession, user_id: int, title: str,
    description: Optional[str] = None, session_id: Optional[UUID] = None,
    due_date: Optional[datetime] = None, status: str = "pending",
) -> UserTask:
    if status not in _VALID_TASK_STATUS:
        raise ConversationError(f"非法任务状态: {status}", status=422)
    if session_id is not None:
        await get_session(db, user_id, session_id)  # 归属校验
    task = UserTask(
        user_id=user_id, title=title, description=description,
        session_id=session_id, due_date=due_date, status=status,
    )
    db.add(task)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("创建任务失败", status=500)
    await db.refresh(task)
    return task


async def list_tasks(
    db: AsyncSession, user_id: int, status_filter: Optional[str] = None,
    limit: int = 100, offset: int = 0,
) -> list[UserTask]:
    stmt = select(UserTask).where(UserTask.user_id == user_id)
    if status_filter:
        stmt = stmt.where(UserTask.status == status_filter)
    stmt = stmt.order_by(UserTask.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_task(
    db: AsyncSession, user_id: int, task_id: int,
    title: Optional[str] = None, description: Optional[str] = None,
    status: Optional[str] = None, due_date: Optional[datetime] = None,
) -> UserTask:
    result = await db.execute(
        select(UserTask).where(UserTask.id == task_id, UserTask.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise ConversationError("任务不存在或无权访问", status=404)
    if status is not None and status not in _VALID_TASK_STATUS:
        raise ConversationError(f"非法任务状态: {status}", status=422)
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        task.status = status
    if due_date is not None:
        task.due_date = due_date
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("更新任务失败", status=500)
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, user_id: int, task_id: int) -> None:
    result = await db.execute(
        delete(UserTask).where(UserTask.id == task_id, UserTask.user_id == user_id)
    )
    if result.rowcount == 0:
        raise ConversationError("任务不存在或无权访问", status=404)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise ConversationError("删除任务失败", status=500)
