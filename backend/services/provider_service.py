"""
AI 供应商配置服务层

CRUD 操作 + API Key 加密/脱敏
"""
from __future__ import annotations

import logging

from sqlalchemy import select, func, delete as sql_delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.provider import AIProvider
from backend.utils.crypto import encrypt, decrypt

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def _mask_api_key(key: str) -> str:
    """API Key 脱敏：显示前4位+后4位，中间用***替代"""
    if len(key) <= 8:
        return "****"
    return key[:4] + "***" + key[-4:]


async def list_providers(db: AsyncSession, user_id: int) -> list[dict]:
    """列出用户的所有供应商配置（API Key 脱敏）"""
    stmt = select(AIProvider).where(AIProvider.user_id == user_id).order_by(AIProvider.created_at.desc())
    result = await db.execute(stmt)
    providers = result.scalars().all()
    return [
        {
            "id": p.id,
            "provider_name": p.provider_name,
            "llm_api_key": _mask_api_key(decrypt(p.llm_api_key) or ""),
            "llm_base_url": p.llm_base_url,
            "llm_model": p.llm_model,
            "embedding_model": p.embedding_model,
            "embedding_dim": p.embedding_dim,
            "is_enabled": p.is_enabled,
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "updated_at": p.updated_at.isoformat() if p.updated_at else "",
        }
        for p in providers
    ]


async def get_provider(db: AsyncSession, user_id: int, provider_id: int) -> dict | None:
    """获取单个供应商详情（API Key 脱敏）"""
    stmt = select(AIProvider).where(
        AIProvider.id == provider_id, AIProvider.user_id == user_id
    )
    result = await db.execute(stmt)
    p = result.scalar_one_or_none()
    if not p:
        return None
    return {
        "id": p.id,
        "provider_name": p.provider_name,
        "llm_api_key": _mask_api_key(decrypt(p.llm_api_key) or ""),
        "llm_base_url": p.llm_base_url,
        "llm_model": p.llm_model,
        "embedding_model": p.embedding_model,
        "embedding_dim": p.embedding_dim,
        "is_enabled": p.is_enabled,
        "created_at": p.created_at.isoformat() if p.created_at else "",
        "updated_at": p.updated_at.isoformat() if p.updated_at else "",
    }


async def create_provider(db: AsyncSession, user_id: int, data: dict) -> dict:
    """创建供应商配置（API Key 加密存储）"""
    provider = AIProvider(
        user_id=user_id,
        provider_name=data["provider_name"],
        llm_api_key=encrypt(data["llm_api_key"]),
        llm_base_url=data["llm_base_url"],
        llm_model=data["llm_model"],
        embedding_model=data["embedding_model"],
        embedding_dim=data["embedding_dim"],
        is_enabled=data.get("is_enabled", True),
    )
    db.add(provider)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("创建供应商失败 user_id=%s", user_id)
        raise ProviderError("创建供应商失败", status=500)
    await db.refresh(provider)

    # 返回脱敏后的数据
    return await get_provider(db, user_id, provider.id)


async def update_provider(db: AsyncSession, user_id: int, provider_id: int, data: dict) -> dict | None:
    """更新供应商配置（仅更新传入字段）"""
    # 先查是否存在
    existing = await get_provider(db, user_id, provider_id)
    if not existing:
        return None

    # 构建更新字典，只更新非None字段
    update_data = {}
    for field in ("provider_name", "llm_base_url", "llm_model", "embedding_model", "embedding_dim", "is_enabled"):
        if field in data and data[field] is not None:
            update_data[field] = data[field]

    # API Key 单独处理：加密后存储
    if data.get("llm_api_key") is not None:
        update_data["llm_api_key"] = encrypt(data["llm_api_key"])

    if not update_data:
        return existing

    stmt = (
        select(AIProvider)
        .where(AIProvider.id == provider_id, AIProvider.user_id == user_id)
    )
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()

    for key, value in update_data.items():
        setattr(provider, key, value)

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("更新供应商失败 provider_id=%s", provider_id)
        raise ProviderError("更新供应商失败", status=500)

    return await get_provider(db, user_id, provider_id)


async def delete_provider(db: AsyncSession, user_id: int, provider_id: int) -> bool:
    """删除供应商配置"""
    stmt = sql_delete(AIProvider).where(
        AIProvider.id == provider_id, AIProvider.user_id == user_id
    )
    result = await db.execute(stmt)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("删除供应商失败 provider_id=%s", provider_id)
        raise ProviderError("删除供应商失败", status=500)
    return result.rowcount > 0


async def toggle_provider(db: AsyncSession, user_id: int, provider_id: int) -> dict | None:
    """切换供应商启用/禁用状态"""
    stmt = select(AIProvider).where(
        AIProvider.id == provider_id, AIProvider.user_id == user_id
    )
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    if not provider:
        return None
    provider.is_enabled = not provider.is_enabled
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("切换供应商状态失败 provider_id=%s", provider_id)
        raise ProviderError("切换供应商状态失败", status=500)
    return await get_provider(db, user_id, provider_id)


async def get_active_provider_config(db: AsyncSession, user_id: int) -> dict | None:
    """
    获取用户当前启用的供应商配置（用于 LightRAG 初始化）

    优先返回 is_enabled=True 的记录；如果有多条启用记录，
    取最近更新的一条。无启用配置时返回 None。
    """
    stmt = (
        select(AIProvider)
        .where(AIProvider.user_id == user_id, AIProvider.is_enabled == True)
        .order_by(AIProvider.updated_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    if not provider:
        return None
    return {
        "id": provider.id,
        "provider_name": provider.provider_name,
        "llm_api_key": decrypt(provider.llm_api_key),  # 返回明文供内部使用
        "llm_base_url": provider.llm_base_url,
        "llm_model": provider.llm_model,
        "embedding_model": provider.embedding_model,
        "embedding_dim": provider.embedding_dim,
    }


async def resolve_provider_config(db: AsyncSession, user_id: int) -> dict | None:
    """
    解析用户生效的供应商配置（唯一配置源：数据库 ai_providers 表）

    优先返回 is_enabled=True 的记录（最近更新优先）。
    无启用配置时返回 None（调用方应提示用户前往设置页配置供应商）。

    返回字典结构：{
        "source": "db",
        "provider_name": str,
        "llm_api_key": str,
        "llm_base_url": str,
        "llm_model": str,
        "embedding_model": str,
        "embedding_dim": int,
    }
    """
    db_config = await get_active_provider_config(db, user_id)
    if db_config:
        return {
            "source": "db",
            "provider_name": db_config["provider_name"],
            "llm_api_key": db_config["llm_api_key"],
            "llm_base_url": db_config["llm_base_url"],
            "llm_model": db_config["llm_model"],
            "embedding_model": db_config["embedding_model"],
            "embedding_dim": db_config["embedding_dim"],
        }
    return None
