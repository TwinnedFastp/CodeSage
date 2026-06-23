"""Function Calling 模块的 Pydantic 数据模型"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolParamField(BaseModel):
    """简化的工具参数 schema 描述"""

    name: str
    type: str = "string"  # string/int/bool/object/array
    required: bool = True
    description: str = ""


class ToolMetadata(BaseModel):
    """工具元数据：名称、描述、参数 schema、是否需要管理员权限"""

    name: str
    description: str = ""
    params: list[ToolParamField] = Field(default_factory=list)
    requires_admin: bool = False


class ToolCallRequest(BaseModel):
    """工具调用请求体"""

    function_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    target_node_id: Optional[str] = None


class ToolCallResult(BaseModel):
    """工具调用结果"""

    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    function_name: str = ""
