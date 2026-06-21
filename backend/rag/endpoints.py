"""
RAG 知识库管理接口（需登录，按用户隔离知识库）

提供：
- GET  /status           检查 LightRAG 是否可用
- POST /documents        写入文本到知识库
- GET  /documents        列出知识库文档
- DELETE /documents/{id} 删除文档
- POST /upload-file      上传文件（MD/TXT）到知识库
- POST /query            查询知识库
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.rag.schemas import (
    RAGDocumentIn,
    RAGQueryIn,
    RAGQueryOut,
    RAGWriteOut,
    FileUploadIn,
    FileUploadOut,
)
from backend.rag.service import lightrag_service
from backend.services.provider_service import resolve_provider_config

router = APIRouter()


async def _get_provider_config_or_raise(db: AsyncSession, user: User) -> dict:
    """获取用户生效的供应商配置，无配置时抛 400 异常"""
    config = await resolve_provider_config(db, user.id)
    if not config:
        raise HTTPException(
            status_code=400,
            detail="未配置 AI 供应商，请在设置页面添加供应商配置。",
        )
    return config


@router.get("/status")
async def rag_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    检查 LightRAG 知识库是否可用（前端用来决定是否显示 RAG 开关）。

    判断逻辑：LIGHTRAG_ENABLED 开启 + 用户有可用供应商配置（DB 或 env）。
    """
    from backend.core.config import settings
    config = await resolve_provider_config(db, user.id)
    has_config = config is not None
    return {
        "enabled": settings.LIGHTRAG_ENABLED,
        "has_provider_config": has_config,
        "config_source": config.get("source", "") if config else "",
        "ready": settings.LIGHTRAG_ENABLED and has_config,
    }


@router.post("/documents", response_model=RAGWriteOut)
async def insert_document(
    payload: RAGDocumentIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RAGWriteOut:
    """将文本写入 LightRAG 知识库（分块 + 实体抽取 + 向量化 + 图谱更新）。"""
    provider_config = await _get_provider_config_or_raise(db, user)

    text = payload.text
    if payload.source:
        text = f"资料来源：{payload.source}\n\n{text}"

    try:
        await lightrag_service.insert_text(user.id, provider_config, text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RAGWriteOut(success=True, message="文本已写入 LightRAG 知识库。")


@router.post("/upload-file", response_model=FileUploadOut)
async def upload_file(
    payload: FileUploadIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileUploadOut:
    """上传文件内容到知识库（前端读取文件后传文本，由 LightRAG 自带逻辑完成分片和向量化）。"""
    provider_config = await _get_provider_config_or_raise(db, user)

    try:
        await lightrag_service.insert_file(
            user.id, provider_config, payload.content, payload.filename, payload.source,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return FileUploadOut(success=True, message=f"文件 {payload.filename} 已写入知识库。")


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出当前用户知识库中已处理的文档。"""
    provider_config = await _get_provider_config_or_raise(db, user)
    try:
        docs = await lightrag_service.list_documents(user.id, provider_config)
        return {"documents": docs, "total": len(docs)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除当前用户知识库中的某个文档及其相关实体/关系/向量。"""
    provider_config = await _get_provider_config_or_raise(db, user)
    try:
        ok = await lightrag_service.delete_document(user.id, provider_config, doc_id)
        if not ok:
            raise HTTPException(status_code=404, detail="文档不存在或删除失败")
        return {"success": True, "message": f"文档 {doc_id} 已删除"}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/query", response_model=RAGQueryOut)
async def query_document(
    payload: RAGQueryIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RAGQueryOut:
    """从 LightRAG 知识库中检索并生成回答。"""
    provider_config = await _get_provider_config_or_raise(db, user)
    try:
        answer = await lightrag_service.query(
            user.id, provider_config, payload.question, mode=payload.mode,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RAGQueryOut(answer=answer, mode=payload.mode)
