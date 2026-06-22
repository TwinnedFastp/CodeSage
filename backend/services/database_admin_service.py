from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.database_admin import DatabaseColumnOut, DatabaseRowListOut, DatabaseTableOut

_ALLOWED_SCHEMA = "public"
_SYSTEM_TABLE_PREFIXES = ("pg_", "sql_")


class DatabaseAdminError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        self.message = message
        self.status = status
        super().__init__(message)


async def list_tables(db: AsyncSession) -> list[DatabaseTableOut]:
    rows = await db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """), {"schema": _ALLOWED_SCHEMA})
    tables: list[DatabaseTableOut] = []
    for (table_name,) in rows.all():
        if _is_system_table(table_name):
            continue
        columns = await list_columns(db, table_name)
        tables.append(DatabaseTableOut(
            name=table_name,
            row_count=await count_rows(db, table_name),
            columns=columns,
        ))
    return tables


async def list_columns(db: AsyncSession, table: str) -> list[DatabaseColumnOut]:
    await _ensure_table_exists(db, table)
    result = await db.execute(text("""
        SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN true ELSE false END AS is_primary_key
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
          ON c.table_schema = kcu.table_schema
         AND c.table_name = kcu.table_name
         AND c.column_name = kcu.column_name
        LEFT JOIN information_schema.table_constraints tc
          ON kcu.constraint_schema = tc.constraint_schema
         AND kcu.constraint_name = tc.constraint_name
         AND tc.constraint_type = 'PRIMARY KEY'
        WHERE c.table_schema = :schema
          AND c.table_name = :table
        ORDER BY c.ordinal_position
    """), {"schema": _ALLOWED_SCHEMA, "table": table})
    return [
        DatabaseColumnOut(
            name=row.column_name,
            data_type=row.data_type,
            is_nullable=row.is_nullable == "YES",
            is_primary_key=bool(row.is_primary_key),
            column_default=row.column_default,
        )
        for row in result.all()
    ]


async def list_rows(
    db: AsyncSession,
    table: str,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
) -> DatabaseRowListOut:
    await _ensure_table_exists(db, table)
    columns = await list_columns(db, table)
    primary_keys = [c.name for c in columns if c.is_primary_key]
    table_sql = _quote_ident(table)
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    where_sql = ""

    if search:
        text_columns = [c.name for c in columns if c.data_type in {"text", "character varying", "character"}]
        if text_columns:
            params["search"] = f"%{search}%"
            where_sql = "WHERE " + " OR ".join(
                f"{_quote_ident(col)} ILIKE :search" for col in text_columns
            )

    total = await count_rows(db, table, where_sql=where_sql, params=params)
    order_sql = _build_order_sql(primary_keys, columns)
    result = await db.execute(text(f"""
        SELECT *
        FROM {table_sql}
        {where_sql}
        {order_sql}
        LIMIT :limit OFFSET :offset
    """), params)
    rows = [_normalize_row(dict(row._mapping)) for row in result.all()]
    return DatabaseRowListOut(
        table=table,
        columns=columns,
        primary_keys=primary_keys,
        rows=rows,
        total=total,
        limit=limit,
        offset=offset,
    )


async def create_row(db: AsyncSession, table: str, values: dict[str, Any]) -> None:
    columns = await list_columns(db, table)
    allowed = {c.name for c in columns}
    clean = _filter_values(values, allowed)
    if not clean:
        raise DatabaseAdminError("没有可写入的字段")
    col_sql = ", ".join(_quote_ident(k) for k in clean.keys())
    val_sql = ", ".join(f":{k}" for k in clean.keys())
    await db.execute(text(f"INSERT INTO {_quote_ident(table)} ({col_sql}) VALUES ({val_sql})"), clean)
    await db.commit()


async def update_row(db: AsyncSession, table: str, primary_key: dict[str, Any], values: dict[str, Any]) -> None:
    columns = await list_columns(db, table)
    pk_names = [c.name for c in columns if c.is_primary_key]
    if not pk_names:
        raise DatabaseAdminError("该表没有主键，暂不支持更新")
    _validate_primary_key(pk_names, primary_key)
    allowed = {c.name for c in columns if c.name not in pk_names}
    clean = _filter_values(values, allowed)
    if not clean:
        raise DatabaseAdminError("没有可更新的字段")

    set_sql = ", ".join(f"{_quote_ident(k)} = :set_{k}" for k in clean.keys())
    where_sql = " AND ".join(f"{_quote_ident(k)} = :pk_{k}" for k in pk_names)
    params = {f"set_{k}": v for k, v in clean.items()}
    params.update({f"pk_{k}": primary_key[k] for k in pk_names})
    result = await db.execute(text(f"UPDATE {_quote_ident(table)} SET {set_sql} WHERE {where_sql}"), params)
    await db.commit()
    if result.rowcount == 0:
        raise DatabaseAdminError("未找到要更新的记录", status=404)


async def delete_row(db: AsyncSession, table: str, primary_key: dict[str, Any]) -> None:
    columns = await list_columns(db, table)
    pk_names = [c.name for c in columns if c.is_primary_key]
    if not pk_names:
        raise DatabaseAdminError("该表没有主键，暂不支持删除")
    _validate_primary_key(pk_names, primary_key)
    where_sql = " AND ".join(f"{_quote_ident(k)} = :pk_{k}" for k in pk_names)
    params = {f"pk_{k}": primary_key[k] for k in pk_names}
    result = await db.execute(text(f"DELETE FROM {_quote_ident(table)} WHERE {where_sql}"), params)
    await db.commit()
    if result.rowcount == 0:
        raise DatabaseAdminError("未找到要删除的记录", status=404)


async def count_rows(
    db: AsyncSession,
    table: str,
    where_sql: str = "",
    params: dict[str, Any] | None = None,
) -> int:
    await _ensure_table_exists(db, table)
    result = await db.execute(text(f"SELECT COUNT(*) FROM {_quote_ident(table)} {where_sql}"), params or {})
    return int(result.scalar() or 0)


async def _ensure_table_exists(db: AsyncSession, table: str) -> None:
    if not table or _is_system_table(table) or not table.replace("_", "").isalnum():
        raise DatabaseAdminError("非法表名")
    result = await db.execute(text("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = :schema
          AND table_name = :table
          AND table_type = 'BASE TABLE'
    """), {"schema": _ALLOWED_SCHEMA, "table": table})
    if not result.scalar_one_or_none():
        raise DatabaseAdminError("表不存在", status=404)


def _quote_ident(name: str) -> str:
    if not name.replace("_", "").isalnum():
        raise DatabaseAdminError("非法标识符")
    return '"' + name.replace('"', '""') + '"'


def _is_system_table(table: str) -> bool:
    return table.startswith(_SYSTEM_TABLE_PREFIXES)


def _build_order_sql(primary_keys: list[str], columns: list[DatabaseColumnOut]) -> str:
    if primary_keys:
        return "ORDER BY " + ", ".join(_quote_ident(k) for k in primary_keys)
    if any(c.name == "created_at" for c in columns):
        return "ORDER BY created_at DESC"
    return ""


def _filter_values(values: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in values.items():
        if key not in allowed:
            continue
        clean[key] = _coerce_value(value)
    return clean


def _validate_primary_key(pk_names: list[str], primary_key: dict[str, Any]) -> None:
    missing = [k for k in pk_names if k not in primary_key]
    if missing:
        raise DatabaseAdminError(f"缺少主键字段：{', '.join(missing)}")


def _coerce_value(value: Any) -> Any:
    if value == "":
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (datetime, date)):
            normalized[key] = value.isoformat()
        elif isinstance(value, Decimal):
            normalized[key] = float(value)
        elif isinstance(value, UUID):
            normalized[key] = str(value)
        elif isinstance(value, (dict, list)):
            normalized[key] = value
        else:
            normalized[key] = value
    return normalized
