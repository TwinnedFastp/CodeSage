from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DatabaseColumnOut(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    column_default: str | None = None


class DatabaseTableOut(BaseModel):
    name: str
    row_count: int | None = None
    columns: list[DatabaseColumnOut] = Field(default_factory=list)


class DatabaseRowListOut(BaseModel):
    table: str
    columns: list[DatabaseColumnOut]
    primary_keys: list[str]
    rows: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


class DatabaseRowCreateIn(BaseModel):
    values: dict[str, Any]


class DatabaseRowUpdateIn(BaseModel):
    primary_key: dict[str, Any]
    values: dict[str, Any]


class DatabaseRowDeleteIn(BaseModel):
    primary_key: dict[str, Any]


class DatabaseMutationOut(BaseModel):
    success: bool = True
    message: str


DatabaseColumnKind = Literal[
    "text", "number", "boolean", "datetime", "json", "uuid", "unknown",
]
