from typing import Any

from pydantic import BaseModel, Field


class NodeExpandIn(BaseModel):
    message: str


class NodeRegenerateIn(BaseModel):
    message: str | None = None


class NodeVersionOut(BaseModel):
    id: str
    version_no: int
    content_json: dict[str, Any] | None = None
    source: str
    created_at: str | None = None


class NodeOut(BaseModel):
    id: str
    conversation_id: str | None = None
    parent_id: str | None = None
    node_type: str
    created_at: str | None = None
    current_version: NodeVersionOut | None = None


class NodeDetailOut(BaseModel):
    node: NodeOut
    versions: list[NodeVersionOut] = Field(default_factory=list)


class NodeActionOut(BaseModel):
    node_id: str
    version_no: int
    component: dict[str, Any]
