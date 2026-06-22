"""
聊天流式接口（LightRAG 知识增强 + 多轮历史记忆 + 动态供应商配置）

设计要点：
1. 需要登录（依赖 get_current_user）
2. 每轮对话会读取会话历史消息，拼成 messages 数组传给 LLM —— 让 AI 真正"记住"上下文
3. 集成 LightRAG：默认检索知识库相关片段，作为 system prompt 的知识背景
4. 供应商配置动态化：从 DB 读取用户启用的供应商配置（API Key / Base URL / 模型），
   无 DB 配置时兜底使用 .env 环境变量
5. 用户消息先落库，流式输出 LLM 回复，流结束后 assistant 回复落库
6. 流结束后保底触发标题生成（前端也会调，二者去重）
7. 无 session_id 时自动创建会话
"""
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.rag.service import lightrag_service
from backend.services import conversation_service
from backend.services.provider_service import resolve_provider_config
from backend.sys_prompts import CHAT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)
router = APIRouter()

# 历史消息上限：取最近 N 条喂给 LLM，避免 token 爆炸
MAX_HISTORY_MESSAGES = 20


async def _persist_message(db: AsyncSession, user_id: int, session_id: str, role: str, content: str):
    """落库一条消息，失败不阻断主流程但记录日志。"""
    try:
        await conversation_service.add_message(db, user_id, session_id, role, content)
    except Exception:
        logger.exception("消息落库失败 user_id=%s session_id=%s role=%s", user_id, session_id, role)


async def _load_history_messages(db: AsyncSession, user_id: int, session_id: str) -> list[dict]:
    """
    读取会话历史消息，映射成 OpenAI messages 格式。

    注意：调用时机要在本轮 user 消息落库之后，这样历史里已包含当前问题，
    传给 LLM 时就不需要再单独 append 当前消息，避免重复。
    """
    try:
        msgs = await conversation_service.list_messages(
            db, user_id, UUID(session_id), limit=MAX_HISTORY_MESSAGES, offset=0,
        )
    except Exception:
        logger.exception("读取历史消息失败 session_id=%s", session_id)
        return []

    history = []
    for m in msgs:
        role = "user" if m.role == "user" else "assistant"
        history.append({"role": role, "content": m.content})
    return history


async def _query_knowledge(
    user_id: int, provider_config: dict, user_message: str, mode: str = "hybrid",
) -> str:
    """
    用 LightRAG 检索知识库，返回相关上下文文本。

    LightRAG 不可用时静默降级（返回空串），不影响普通对话。
    """
    from backend.core.config import settings
    if not settings.LIGHTRAG_ENABLED:
        return ""
    try:
        return await lightrag_service.query(user_id, provider_config, user_message, mode=mode)
    except Exception:
        logger.exception("LightRAG 知识检索失败，降级为纯对话 user_id=%s", user_id)
        return ""


def _build_system_prompt(knowledge: str, use_rag: bool) -> str:
    """构建 system prompt，根据是否启用 RAG 决定是否注入知识背景。"""
    base = CHAT_SYSTEM_PROMPT
    if use_rag and knowledge and knowledge.strip():
        return (
            base
            + "\n\n**知识库检索（RAG 模式已开启）**"
            + f"\n本次从知识库检索到以下相关资料，请在回答时参考并适当引用：\n---\n{knowledge.strip()}\n---"
        )
    return base


async def ai_response_generator(
    history: list[dict],
    user_message: str,
    provider_config: dict,
    knowledge: str = "",
    use_rag: bool = False,
):
    """
    大模型流式回复生成器。

    - history: 已包含当前 user 消息的历史数组（OpenAI messages 格式）
    - provider_config: 用户的供应商配置（含 API Key / Base URL / 模型名）
    - knowledge: LightRAG 检索到的知识上下文（可空）
    - use_rag: 是否处于 RAG 模式
    """
    api_key = provider_config.get("llm_api_key", "")
    base_url = provider_config.get("llm_base_url", "")
    llm_model = provider_config.get("llm_model", "")

    if not api_key:
        yield f"data: {json.dumps({'content': '未配置大模型 API Key，请在设置页面添加供应商配置。'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # 每次请求按用户配置创建独立的 OpenAI 客户端
    # （AsyncOpenAI 内部有连接池，轻量创建无性能问题）
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    system_prompt = _build_system_prompt(knowledge, use_rag)
    messages = [{"role": "system", "content": system_prompt}] + history

    try:
        response = await client.chat.completions.create(
            model=llm_model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield f"data: {json.dumps({'content': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
    except Exception as e:
        logger.exception("调用大模型失败 model=%s base_url=%s", llm_model, base_url)
        yield f"data: {json.dumps({'content': f'调用大模型发生错误：{str(e)}'}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


async def _maybe_auto_title(
    db: AsyncSession, user_id: int, session_id: str,
    current_title: str | None, provider_config: dict,
) -> str | None:
    """
    流结束后保底触发标题生成。

    触发条件：标题为空 / 仍是默认 "新会话"。
    成功返回新标题，失败返回 None（前端调用作为补充，二者通过 titleGeneratedSessions 去重）。
    """
    if current_title and current_title != "新会话":
        return None
    try:
        updated = await conversation_service.generate_title(
            db, user_id, UUID(session_id), provider_config=provider_config,
        )
        return updated.title
    except Exception:
        logger.debug("保底标题生成跳过 session_id=%s", session_id)
        return None


async def _streaming_with_persistence(
    user_message: str, session_id: str, user_id: int, db: AsyncSession,
    provider_config: dict, use_rag: bool, mode: str,
):
    """
    流式生成 + 落库 + 保底标题：
    1. 用户消息先落库
    2. 读取历史（已含本轮 user 消息）
    3. LightRAG 检索知识（仅当 use_rag=true 时，用户显式开启 RAG 模式）
    4. 流式输出 LLM 回复
    5. assistant 回复落库
    6. 保底触发标题生成
    """
    # 1. 用户消息落库
    await _persist_message(db, user_id, session_id, "user", user_message)

    # 2. 读取历史（已包含本轮 user 消息）
    history = await _load_history_messages(db, user_id, session_id)

    # 3. 知识检索：只有用户显式开启 RAG 模式才检索
    knowledge = ""
    if use_rag:
        knowledge = await _query_knowledge(user_id, provider_config, user_message, mode)

    # 4 & 5. 流式生成 + 收集完整回复
    full_reply_parts: list[str] = []
    async for chunk in ai_response_generator(history, user_message, provider_config, knowledge, use_rag):
        if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
            data = chunk[6:].strip()
            try:
                parsed = json.loads(data)
                if parsed.get("content"):
                    full_reply_parts.append(parsed["content"])
            except Exception:
                pass
        yield chunk

    # 5. assistant 回复落库
    full_reply = "".join(full_reply_parts)
    if full_reply:
        await _persist_message(db, user_id, session_id, "assistant", full_reply)

    # 6. 保底标题生成，并通过 SSE 把新标题推给前端
    try:
        session = await conversation_service.get_session(db, user_id, UUID(session_id))
        new_title = await _maybe_auto_title(
            db, user_id, session_id, session.title, provider_config,
        )
        if new_title:
            yield f"data: {json.dumps({'title': new_title, 'session_id': session_id}, ensure_ascii=False)}\n\n"
    except Exception:
        logger.debug("读取会话标题失败，跳过保底生成 session_id=%s", session_id)


@router.post("/stream")
async def chat_streaming(
    request: Request,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    流式对话接口（需登录）

    请求体：{ message, session_id?, use_rag?, mode? }
    - 无 session_id 时自动创建会话
    - 自动读取历史消息让 AI 记住上下文
    - 供应商配置从 DB 动态读取（用户在设置页配置），无配置时兜底 .env
    - 默认集成 LightRAG 知识检索（可通过 use_rag=false 关闭）
    - 用户消息与 assistant 回复自动落库
    """
    message = payload.get("message", "")
    use_rag = bool(payload.get("use_rag", False))
    mode = payload.get("mode", "hybrid")
    session_id = payload.get("session_id")

    if not message:
        return JSONResponse(status_code=422, content={"message": "消息不能为空"})

    # 解析用户生效的供应商配置（唯一来源：数据库 ai_providers 表）
    provider_config = await resolve_provider_config(db, user.id)
    if not provider_config:
        return JSONResponse(
            status_code=400,
            content={"message": "未配置 AI 供应商，请在设置页面添加供应商配置。"},
        )

    # 无会话则自动创建
    if not session_id:
        try:
            session = await conversation_service.create_session(db, user.id, message[:32])
            session_id = str(session.id)
        except Exception:
            logger.exception("创建会话失败")
            return JSONResponse(status_code=500, content={"message": "创建会话失败"})

    # 透传 session_id 给前端（通过首个 SSE 事件）
    async def wrapped():
        yield f"data: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"
        async for chunk in _streaming_with_persistence(
            message, session_id, user.id, db, provider_config, use_rag, mode,
        ):
            yield chunk

    return StreamingResponse(wrapped(), media_type="text/event-stream")
