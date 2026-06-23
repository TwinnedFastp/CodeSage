from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.schemas.node import NodeActionOut, NodeDetailOut, NodeExpandIn, NodeRegenerateIn
from backend.services.conversation_service import build_short_term_messages
from backend.services import node_service

router = APIRouter()


async def _load_node_history(db: AsyncSession, user_id: int, node_detail: dict | None) -> list[dict]:
    conversation_id = None
    if node_detail:
        conversation_id = node_detail.get("node", {}).get("conversation_id")
    if not conversation_id:
        return []
    try:
        return await build_short_term_messages(db, user_id, UUID(conversation_id), limit=20)
    except Exception:
        return []


@router.get("/{node_id}", response_model=NodeDetailOut)
async def get_node_detail(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        node_uuid = UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="节点不存在")

    detail = await node_service.get_node_with_versions(db, user.id, node_uuid)
    if not detail:
        raise HTTPException(status_code=404, detail="节点不存在")
    return detail


@router.get("/by-session/{session_id}")
async def list_nodes_by_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出某会话下的所有生成式节点（含当前版本内容），用于生成式页面加载历史。"""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="会话不存在")
    nodes = await node_service.list_nodes_by_conversation(db, user.id, session_uuid)
    return {"nodes": nodes}


@router.post("/{node_id}/expand", response_model=NodeActionOut)
async def expand_node(
    node_id: str,
    payload: NodeExpandIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        node_uuid = UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="节点不存在")

    detail = await node_service.get_node_with_versions(db, user.id, node_uuid)
    if not detail:
        raise HTTPException(status_code=404, detail="节点不存在")

    history = await _load_node_history(db, user.id, detail)
    try:
        node, version, protocol = await node_service.expand_node(
            db, user.id, node_uuid, history, payload.message
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return NodeActionOut(
        node_id=str(node.id),
        version_no=version.version_no,
        component=protocol.model_dump(mode="json"),
    )


@router.post("/{node_id}/regenerate", response_model=NodeActionOut)
async def regenerate_node(
    node_id: str,
    payload: NodeRegenerateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        node_uuid = UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="节点不存在")

    detail = await node_service.get_node_with_versions(db, user.id, node_uuid)
    if not detail:
        raise HTTPException(status_code=404, detail="节点不存在")

    history = await _load_node_history(db, user.id, detail)
    try:
        node, version, protocol = await node_service.regenerate_node(
            db, user.id, node_uuid, history, instruction=payload.message
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return NodeActionOut(
        node_id=str(node.id),
        version_no=version.version_no,
        component=protocol.model_dump(mode="json"),
    )
