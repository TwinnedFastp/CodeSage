"""
AI 供应商配置管理接口

CRUD + 启用/禁用切换，均需登录认证，按 user_id 隔离。
增删改操作后会失效该用户的 LightRAG 实例缓存，确保下次请求用新配置重建。
"""
from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.rag.service import lightrag_service
from backend.schemas.provider import ProviderCreate, ProviderOut, ProviderUpdate
from backend.services import provider_service

router = APIRouter()


def _err(exc: provider_service.ProviderError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"message": exc.message})


@router.get("", response_model=list[ProviderOut])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出当前用户的所有 AI 供应商配置"""
    return await provider_service.list_providers(db, user.id)


@router.post("", response_model=ProviderOut, status_code=status.HTTP_201_CREATED)
async def create_provider(
    payload: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """新增 AI 供应商配置"""
    try:
        result = await provider_service.create_provider(db, user.id, payload.model_dump())
        # 新增配置可能影响 LightRAG 实例（如果新增的是启用配置），失效缓存
        await lightrag_service.invalidate_user(user.id)
        return result
    except provider_service.ProviderError as exc:
        return _err(exc)


@router.get("/{provider_id}", response_model=ProviderOut)
async def get_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取单个供应商配置详情"""
    result = await provider_service.get_provider(db, user.id, provider_id)
    if not result:
        return JSONResponse(status_code=404, content={"message": "供应商不存在"})
    return result


@router.put("/{provider_id}", response_model=ProviderOut)
async def update_provider(
    provider_id: int,
    payload: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新供应商配置（部分更新）"""
    try:
        result = await provider_service.update_provider(
            db, user.id, provider_id, payload.model_dump(exclude_unset=True),
        )
        if not result:
            return JSONResponse(status_code=404, content={"message": "供应商不存在"})
        # 配置变更后失效 LightRAG 缓存（模型/Key/Base URL 变了都要重建实例）
        await lightrag_service.invalidate_user(user.id)
        return result
    except provider_service.ProviderError as exc:
        return _err(exc)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除供应商配置"""
    try:
        ok = await provider_service.delete_provider(db, user.id, provider_id)
        if not ok:
            return JSONResponse(status_code=404, content={"message": "供应商不存在"})
        # 删除的是启用配置时，需要重建实例（会兜底到 env 或其他启用配置）
        await lightrag_service.invalidate_user(user.id)
    except provider_service.ProviderError as exc:
        return _err(exc)


@router.patch("/{provider_id}/toggle", response_model=ProviderOut)
async def toggle_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """切换供应商启用/禁用状态"""
    try:
        result = await provider_service.toggle_provider(db, user.id, provider_id)
        if not result:
            return JSONResponse(status_code=404, content={"message": "供应商不存在"})
        # 启用/禁用状态变化会影响 resolve_provider_config 的返回结果，失效缓存
        await lightrag_service.invalidate_user(user.id)
        return result
    except provider_service.ProviderError as exc:
        return _err(exc)
