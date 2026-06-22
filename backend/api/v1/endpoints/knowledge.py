from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.rag.service import lightrag_service
from backend.schemas.knowledge import KnowledgeIngestIn, KnowledgeIngestOut, KnowledgeQueryIn, KnowledgeQueryOut
from backend.services.provider_service import resolve_provider_config

router = APIRouter()


@router.post("/ingest", response_model=KnowledgeIngestOut)
async def ingest_knowledge(
    payload: KnowledgeIngestIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    provider_config = await resolve_provider_config(db, user.id)
    if not provider_config:
        raise HTTPException(status_code=400, detail="未配置 AI 供应商")

    text = payload.text
    if payload.source:
        text = f"资料来源：{payload.source}\n\n{text}"

    try:
        status, summary = await lightrag_service.insert_text(user.id, provider_config, text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    success = status in {"success", "processed"}
    message = summary or status
    return KnowledgeIngestOut(success=success, message=message)


@router.post("/query", response_model=KnowledgeQueryOut)
async def query_knowledge(
    payload: KnowledgeQueryIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    provider_config = await resolve_provider_config(db, user.id)
    if not provider_config:
        raise HTTPException(status_code=400, detail="未配置 AI 供应商")

    try:
        answer = await lightrag_service.query(
            user.id, provider_config, payload.question, mode=payload.mode
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return KnowledgeQueryOut(answer=answer, mode=payload.mode)
