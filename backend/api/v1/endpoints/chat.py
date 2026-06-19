from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
import asyncio
import json

router = APIRouter()

async def mock_ai_response_generator(user_message: str):
    """
    模拟 AI 流式回复的生成器
    """
    responses = [
        "你好！我是你的 AI 助手。",
        f"你刚才说：'{user_message}'。",
        "这是一个流式输出的示例。",
        "我可以逐字逐句地回复你，就像 ChatGPT 一样。",
        "如果你有任何问题，请随时问我！"
    ]
    
    for text in responses:
        # 模拟思考时间
        await asyncio.sleep(0.5)
        # 以 SSE (Server-Sent Events) 格式返回数据
        # 或者直接返回文本块，前端按需处理
        yield f"data: {json.dumps({'content': text + ' '})}\n\n"
    
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
    return StreamingResponse(
        mock_ai_response_generator(message),
        media_type="text/event-stream"
    )
