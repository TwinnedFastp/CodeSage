"""工具参数与权限校验"""
from __future__ import annotations

from typing import Any

from backend.function_calling.exceptions import (
    ToolNotFoundError,
    ToolPermissionError,
    ToolValidationError,
)
from backend.function_calling.registry import ToolFunc, ToolRegistry
from backend.function_calling.schemas import ToolMetadata


def validate_params(metadata: ToolMetadata, params: Any) -> None:
    """校验工具参数：仅检查必填字段存在性，不做严格类型转换"""
    if not isinstance(params, dict):
        raise ToolValidationError("工具参数必须是对象")

    for field in metadata.params:
        if field.required and field.name not in params:
            raise ToolValidationError(f"缺少必填参数: {field.name}")


def validate_tool_call(
    registry: ToolRegistry,
    function_name: str,
    params: dict,
    user: Any,
) -> tuple[ToolMetadata, ToolFunc]:
    """校验工具调用：存在性 → 参数 → 权限，返回 (metadata, func)"""
    tool = registry.get(function_name)
    if tool is None:
        raise ToolNotFoundError(f"未注册的工具: {function_name}")

    metadata, func = tool
    validate_params(metadata, params)

    if metadata.requires_admin and not getattr(user, "is_admin", False):
        raise ToolPermissionError(f"工具 {function_name} 需要管理员权限")

    return tool
