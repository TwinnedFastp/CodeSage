"""
RAG 知识库管理接口

提供：
- POST /documents        写入文本到知识库
- GET  /documents        列出知识库文档
- DELETE /documents/{id} 删除文档
- POST /query            查询知识库
- GET  /status           检查 LightRAG 是否可用
"""
from fastapi import APIRouter, HTTPException

from backend.schemas.rag import RAGDocumentIn, RAGQueryIn, RAGQueryOut, RAGWriteOut
from backend.services.lightrag_service import lightrag_service

router = APIRouter()


@router.get("/status")
async def rag_status():
    """检查 LightRAG 知识库是否可用（前端用来决定是否显示 RAG 开关）。"""
    from backend.core.config import settings
    return {
        "enabled": settings.LIGHTRAG_ENABLED,
        "has_api_key": bool(settings.lightrag_api_key),
        "ready": settings.LIGHTRAG_ENABLED and bool(settings.lightrag_api_key),
    }


@router.post("/documents", response_model=RAGWriteOut)
async def insert_document(payload: RAGDocumentIn) -> RAGWriteOut:
    """将文本写入 LightRAG 知识库（分块 + 实体抽取 + 向量化 + 图谱更新）。"""
    text = payload.text
    if payload.source:
        text = f"资料来源：{payload.source}\n\n{text}"

    try:
        await lightrag_service.insert_text(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RAGWriteOut(success=True, message="文本已写入 LightRAG 知识库。")


@router.get("/documents")
async def list_documents():
    """列出知识库中已处理的文档。"""
    try:
        docs = await lightrag_service.list_documents()
        return {"documents": docs, "total": len(docs)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除知识库中的某个文档及其相关实体/关系/向量。"""
    try:
        ok = await lightrag_service.delete_document(doc_id)
        if not ok:
            raise HTTPException(status_code=404, detail="文档不存在或删除失败")
        return {"success": True, "message": f"文档 {doc_id} 已删除"}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/query", response_model=RAGQueryOut)
async def query_document(payload: RAGQueryIn) -> RAGQueryOut:
    """从 LightRAG 知识库中检索并生成回答。"""
    try:
        answer = await lightrag_service.query(payload.question, mode=payload.mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RAGQueryOut(answer=answer, mode=payload.mode)
