from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.services.lightrag_service import lightrag_service
from backend.core.config import settings
import asyncio
import json
from openai import AsyncOpenAI

router = APIRouter()

client = AsyncOpenAI(
    api_key=settings.lightrag_api_key,
    base_url=settings.lightrag_base_url
)

async def ai_response_generator(user_message: str):
    """
    大模型流式回复生成器
    """
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
    """
    LightRAG 版流式回复。

    LightRAG 默认返回完整答案，不一定原生支持逐 token 流式输出。
    为了兼容前端现有 SSE 读取方式，这里先拿到完整答案，再按句子/小块发送。
    """
    try:
        answer = await lightrag_service.query(user_message, mode=mode)
    except RuntimeError as exc:
        yield f"data: {json.dumps({'content': f'LightRAG 暂不可用：{exc}'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # 按较小文本块输出，让前端仍然有“正在生成”的体验。
    chunk_size = 32
    for index in range(0, len(answer), chunk_size):
        await asyncio.sleep(0.05)
        chunk = answer[index:index + chunk_size]
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"

@router.post("/chatstreaming")
async def chat_streaming(
    user_input: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    流式对话接口
    """
    message = user_input.get("message", "")
    use_rag = bool(user_input.get("use_rag", False))
    mode = user_input.get("mode", "hybrid")

    if use_rag:
        return StreamingResponse(
            rag_response_generator(message, mode=mode),
            media_type="text/event-stream"
        )

    return StreamingResponse(
        ai_response_generator(message),
        media_type="text/event-stream"
    )
