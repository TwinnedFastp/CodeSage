from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.database_admin import (
    DatabaseMutationOut,
    DatabaseRowCreateIn,
    DatabaseRowDeleteIn,
    DatabaseRowListOut,
    DatabaseRowUpdateIn,
    DatabaseTableOut,
)
from backend.services import database_admin_service
from backend.services.database_admin_service import DatabaseAdminError

router = APIRouter()


def _raise_admin_error(exc: DatabaseAdminError) -> None:
    raise HTTPException(status_code=exc.status, detail=exc.message) from exc


@router.get("/tables", response_model=list[DatabaseTableOut])
async def list_database_tables(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DatabaseTableOut]:
    """列出 public schema 下可管理的数据表。"""
    try:
        return await database_admin_service.list_tables(db)
    except DatabaseAdminError as exc:
        _raise_admin_error(exc)


@router.get("/tables/{table}/rows", response_model=DatabaseRowListOut)
async def list_database_rows(
    table: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DatabaseRowListOut:
    """分页读取某张表的数据行，只支持参数化查询，不开放任意 SQL。"""
    try:
        return await database_admin_service.list_rows(db, table, limit, offset, search)
    except DatabaseAdminError as exc:
        _raise_admin_error(exc)


@router.post("/tables/{table}/rows", response_model=DatabaseMutationOut)
async def create_database_row(
    table: str,
    payload: DatabaseRowCreateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DatabaseMutationOut:
    """新增一行记录。"""
    try:
        await database_admin_service.create_row(db, table, payload.values)
    except DatabaseAdminError as exc:
        _raise_admin_error(exc)
    return DatabaseMutationOut(message="记录已新增")


@router.put("/tables/{table}/rows", response_model=DatabaseMutationOut)
async def update_database_row(
    table: str,
    payload: DatabaseRowUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DatabaseMutationOut:
    """按主键更新一行记录。"""
    try:
        await database_admin_service.update_row(db, table, payload.primary_key, payload.values)
    except DatabaseAdminError as exc:
        _raise_admin_error(exc)
    return DatabaseMutationOut(message="记录已更新")


@router.delete("/tables/{table}/rows", response_model=DatabaseMutationOut)
async def delete_database_row(
    table: str,
    payload: DatabaseRowDeleteIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DatabaseMutationOut:
    """按主键删除一行记录。"""
    try:
        await database_admin_service.delete_row(db, table, payload.primary_key)
    except DatabaseAdminError as exc:
        _raise_admin_error(exc)
    return DatabaseMutationOut(message="记录已删除")
