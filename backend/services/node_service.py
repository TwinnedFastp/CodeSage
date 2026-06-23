"""
UI 节点服务

围绕 UiNode / UiNodeVersion 提供节点树与版本管理：
- create_node / append_version: 节点与版本的基础写入
- create_root_from_chat / regenerate_node / expand_node: 结合 LLM 生成组件协议
- get_node_with_versions: 节点详情与版本列表
- append_tool_result_version: 工具调用结果以特殊版本写入
"""
from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ui_node import UiNode, UiNodeVersion
from backend.schemas.component import ComponentProtocol, validate_component_protocol
from backend.services import component_service
from backend.sys_prompts import REGENERATE_INSTRUCTION, EXPAND_INSTRUCTION

logger = logging.getLogger(__name__)


async def create_node(
    db: AsyncSession,
    user_id: int,
    conversation_id: Any = None,
    parent_id: Any = None,
    node_type: str = "root",
) -> UiNode:
    """创建节点并 flush（未提交，由调用方决定提交时机）。"""
    node = UiNode(
        user_id=user_id,
        conversation_id=conversation_id,
        parent_id=parent_id,
        node_type=node_type,
    )
    db.add(node)
    await db.flush()
    return node


async def _max_version_no(db: AsyncSession, node_id) -> int:
    stmt = select(func.coalesce(func.max(UiNodeVersion.version_no), 0)).where(
        UiNodeVersion.node_id == node_id
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def append_version(
    db: AsyncSession,
    node: UiNode,
    content_json: dict,
    source: str = "llm",
    max_retries: int = 3,
) -> UiNodeVersion:
    """追加新版本，更新节点 current_version_id 后提交。"""
    for attempt in range(max_retries):
        try:
            next_no = await _max_version_no(db, node.id) + 1
            v = UiNodeVersion(
                node_id=node.id,
                version_no=next_no,
                content_json=content_json,
                source=source,
            )
            db.add(v)
            await db.flush()
            node.current_version_id = v.id
            await db.flush()
            await db.commit()
            return v
        except IntegrityError:
            await db.rollback()
            if attempt == max_retries - 1:
                raise
            logger.warning(
                "版本号冲突 node_id=%s attempt=%d/%d", node.id, attempt + 1, max_retries
            )


async def get_node(db: AsyncSession, user_id: int, node_id) -> UiNode | None:
    stmt = select(UiNode).where(UiNode.id == node_id, UiNode.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_version(db: AsyncSession, node_id, version_id) -> UiNodeVersion | None:
    stmt = select(UiNodeVersion).where(
        UiNodeVersion.id == version_id,
        UiNodeVersion.node_id == node_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_active_version(db: AsyncSession, node_id) -> UiNodeVersion | None:
    node_stmt = select(UiNode).where(UiNode.id == node_id)
    node_result = await db.execute(node_stmt)
    node = node_result.scalar_one_or_none()
    if node and node.current_version_id:
        current_version = await get_version(db, node_id, node.current_version_id)
        if current_version:
            return current_version

    stmt = (
        select(UiNodeVersion)
        .where(UiNodeVersion.node_id == node_id)
        .order_by(UiNodeVersion.version_no.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_versions(db: AsyncSession, node_id) -> list[UiNodeVersion]:
    stmt = (
        select(UiNodeVersion)
        .where(UiNodeVersion.node_id == node_id)
        .order_by(UiNodeVersion.version_no.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def activate_version(
    db: AsyncSession,
    user_id: int,
    node_id,
    version_id,
) -> tuple[UiNode, UiNodeVersion]:
    node = await get_node(db, user_id, node_id)
    if not node:
        raise ValueError("节点不存在或无权访问")

    version = await get_version(db, node.id, version_id)
    if not version:
        raise ValueError("版本不存在或不属于该节点")

    node.current_version_id = version.id
    await db.flush()
    await db.commit()
    return node, version


def _version_dict(v: UiNodeVersion) -> dict:
    return {
        "id": str(v.id),
        "version_no": v.version_no,
        "content_json": v.content_json,
        "source": v.source,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


def _version_summary(v: UiNodeVersion) -> dict:
    return {
        "id": str(v.id),
        "version_no": v.version_no,
        "content_json": v.content_json,
        "source": v.source,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


def _node_dict(node: UiNode, cur: UiNodeVersion | None) -> dict:
    return {
        "id": str(node.id),
        "conversation_id": str(node.conversation_id) if node.conversation_id else None,
        "parent_id": str(node.parent_id) if node.parent_id else None,
        "node_type": node.node_type,
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "current_version": _version_dict(cur) if cur else None,
    }


async def get_node_with_versions(
    db: AsyncSession, user_id: int, node_id
) -> dict | None:
    node = await get_node(db, user_id, node_id)
    if not node:
        return None
    cur = await get_active_version(db, node.id)
    versions = await list_versions(db, node.id)
    return {
        "node": _node_dict(node, cur),
        "versions": [_version_summary(v) for v in versions],
    }


async def list_nodes_by_conversation(
    db: AsyncSession, user_id: int, conversation_id
) -> list[dict]:
    """
    列出某会话下的所有节点（含当前版本内容），用于生成式页面加载历史。

    按 created_at 升序返回，前端按顺序还原对话流。
    """
    stmt = (
        select(UiNode)
        .where(UiNode.user_id == user_id, UiNode.conversation_id == conversation_id)
        .order_by(UiNode.created_at.asc())
    )
    result = await db.execute(stmt)
    nodes = list(result.scalars().all())

    out = []
    for node in nodes:
        cur = await get_active_version(db, node.id)
        out.append({
            "node": _node_dict(node, cur),
            "versions": [],  # 列表场景不返回全部版本，按需加载
        })
    return out


async def create_root_from_chat(
    db: AsyncSession,
    user_id: int,
    conversation_id,
    history_messages: list[dict],
    instruction: str,
    context_text: str = "",
) -> tuple[UiNode, UiNodeVersion, ComponentProtocol]:
    """基于对话创建根节点并生成首版组件协议。"""
    node = await create_node(
        db, user_id, conversation_id=conversation_id, parent_id=None, node_type="root"
    )
    protocol = await component_service.generate_component_protocol(
        db, user_id, history_messages, instruction, context_text
    )
    v = await append_version(db, node, protocol.model_dump(mode="json"), source="llm")
    return node, v, protocol


async def regenerate_node(
    db: AsyncSession,
    user_id: int,
    node_id,
    history_messages: list[dict],
    instruction: str | None = None,
    context_text: str = "",
) -> tuple[UiNode, UiNodeVersion, ComponentProtocol]:
    """基于现有节点最新版本重新生成，追加新版本。"""
    node = await get_node(db, user_id, node_id)
    if not node:
        raise ValueError("节点不存在或无权访问")
    cur = await get_active_version(db, node.id)
    ctx = context_text or (json.dumps(cur.content_json, ensure_ascii=False) if cur else "")
    instr = instruction or REGENERATE_INSTRUCTION
    protocol = await component_service.generate_component_protocol(
        db, user_id, history_messages, instr, ctx
        
    )
    v = await append_version(db, node, protocol.model_dump(mode="json"), source="regenerate")
    return node, v, protocol


async def expand_node(
    db: AsyncSession,
    user_id: int,
    parent_node_id,
    history_messages: list[dict],
    instruction: str,
    context_text: str = "",
) -> tuple[UiNode, UiNodeVersion, ComponentProtocol]:
    """基于父节点展开子节点，并生成子节点首版组件协议。"""
    parent = await get_node(db, user_id, parent_node_id)
    if not parent:
        raise ValueError("父节点不存在或无权访问")
    cur = await get_active_version(db, parent.id)
    ctx = context_text or (json.dumps(cur.content_json, ensure_ascii=False) if cur else "")
    child = await create_node(
        db, user_id,
        conversation_id=parent.conversation_id,
        parent_id=parent.id,
        node_type="expand",
    )
    protocol = await component_service.generate_component_protocol(
        db, user_id, history_messages, instruction, ctx
    )
    v = await append_version(db, child, protocol.model_dump(mode="json"), source="expand")
    return child, v, protocol


async def append_tool_result_version(
    db: AsyncSession,
    user_id: int,
    node_id,
    function_name: str,
    result: Any,
) -> tuple[UiNode, UiNodeVersion]:
    """将工具调用结果以 page_type=tool_result 的特殊版本写入节点。"""
    node = await get_node(db, user_id, node_id)
    if not node:
        raise ValueError("节点不存在或无权访问")
    content = {
        "page_type": "tool_result",
        "title": function_name,
        "components": [
            {"type": "text_block", "props": {"content": str(result)}}
        ],
        "actions": [],
        "meta": {"function_name": function_name, "source": "tool"},
    }
    v = await append_version(db, node, content, source="tool")
    return node, v
