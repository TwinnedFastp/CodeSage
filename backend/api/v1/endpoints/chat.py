"""
聊天流式接口

改造点：
- 需要登录（依赖 get_current_user）
- 接收 session_id，把用户消息先存库
- 流式输出 LLM 回复，流结束后把完整 assistant 回复存库
- 无 session_id 时自动创建会话
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.services import conversation_service, lightrag_service
from backend.core.config import settings
import asyncio
import json
from openai import AsyncOpenAI

router = APIRouter()

client = AsyncOpenAI(
    api_key=settings.lightrag_api_key,
    base_url=settings.lightrag_base_url
)


async def _persist_message(db: AsyncSession, user_id: int, session_id: str, role: str, content: str):
    """落库一条消息，失败不阻断主流程。"""
    try:
        await conversation_service.add_message(db, user_id, session_id, role, content)
    except Exception:
        # 落库失败不影响流式回复，仅记录
        pass


async def ai_response_generator(user_message: str):
    """大模型流式回复生成器"""
    if not settings.lightrag_api_key:
        yield f"data: {json.dumps({'content': '未配置大模型 API Key。'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": user_message}],
            stream=True
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield f"data: {json.dumps({'content': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'content': f'调用大模型发生错误：{str(e)}'}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


async def rag_response_generator(user_message: str, mode: str = "hybrid"):
    """LightRAG 版流式回复"""
    try:
        answer = await lightrag_service.query(user_message, mode=mode)
    except RuntimeError as exc:
        yield f"data: {json.dumps({'content': f'LightRAG 暂不可用：{exc}'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    chunk_size = 32
    for index in range(0, len(answer), chunk_size):
        await asyncio.sleep(0.05)
        chunk = answer[index:index + chunk_size]
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


async def _streaming_with_persistence(
    user_message: str, session_id: str, user_id: int, db: AsyncSession,
    use_rag: bool, mode: str,
):
    """
    流式生成 + 落库：
    1. 用户消息先落库
    2. 流式输出 LLM 回复
    3. 流结束后把完整 assistant 回复落库
    """
    # 1. 用户消息落库
    await _persist_message(db, user_id, session_id, "user", user_message)

    # 2. 收集完整回复用于落库
    full_reply_parts: list[str] = []

    generator = rag_response_generator(user_message, mode) if use_rag else ai_response_generator(user_message)
    async for chunk in generator:
        # 旁路收集 content
        if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
            data = chunk[6:].strip()
            try:
                parsed = json.loads(data)
                if parsed.get("content"):
                    full_reply_parts.append(parsed["content"])
            except Exception:
                pass
        yield chunk

    # 3. assistant 回复落库
    full_reply = "".join(full_reply_parts)
    if full_reply:
        await _persist_message(db, user_id, session_id, "assistant", full_reply)


@router.post("/chatstreaming")
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
    - 用户消息与 assistant 回复自动落库到对应会话
    """
    message = payload.get("message", "")
    use_rag = bool(payload.get("use_rag", False))
    mode = payload.get("mode", "hybrid")
    session_id = payload.get("session_id")

    if not message:
        return JSONResponse(status_code=422, content={"message": "消息不能为空"})

    # 无会话则自动创建
    if not session_id:
        try:
            session = await conversation_service.create_session(db, user.id, message[:32])
            session_id = str(session.id)
        except Exception:
            return JSONResponse(status_code=500, content={"message": "创建会话失败"})

    # 透传 session_id 给前端（通过首个 SSE 事件）
    async def wrapped():
        yield f"data: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"
        async for chunk in _streaming_with_persistence(message, session_id, user.id, db, use_rag, mode):
            yield chunk

    return StreamingResponse(wrapped(), media_type="text/event-stream")
