from fastapi import APIRouter, HTTPException

from backend.schemas.rag import RAGDocumentIn, RAGQueryIn, RAGQueryOut, RAGWriteOut
from backend.services.lightrag_service import lightrag_service

router = APIRouter()


@router.post("/documents", response_model=RAGWriteOut)
async def insert_document(payload: RAGDocumentIn) -> RAGWriteOut:
    """
    将文本写入 LightRAG 知识库。

    学习重点：
    - API 层只校验和接收参数。
    - 真正的 LightRAG 写入逻辑交给 service 层。
    """
    text = payload.text
    if payload.source:
        # 把来源也写进文本，后面回答时模型更容易说明信息来自哪里。
        text = f"资料来源：{payload.source}\n\n{text}"

    try:
        await lightrag_service.insert_text(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RAGWriteOut(success=True, message="文本已写入 LightRAG 知识库。")


@router.post("/query", response_model=RAGQueryOut)
async def query_document(payload: RAGQueryIn) -> RAGQueryOut:
    """
    从 LightRAG 知识库中检索并生成回答。
    """
    try:
        answer = await lightrag_service.query(payload.question, mode=payload.mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RAGQueryOut(answer=answer, mode=payload.mode)
