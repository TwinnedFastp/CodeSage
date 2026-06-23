"""工具注册表：管理工具元数据与执行函数的映射"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from backend.function_calling.schemas import ToolMetadata

logger = logging.getLogger(__name__)

# 工具执行函数签名：(params, context) -> result
ToolFunc = Callable[[dict, dict], Awaitable[Any]]


class ToolRegistry:
    """工具注册表，模块级单例维护 name -> (metadata, func) 映射"""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolMetadata, ToolFunc]] = {}

    def register(self, metadata: ToolMetadata, func: ToolFunc) -> None:
        """注册工具；重名覆盖并记录 warn 日志"""
        if metadata.name in self._tools:
            logger.warning("工具 %s 被重复注册，旧实现将被覆盖", metadata.name)
        self._tools[metadata.name] = (metadata, func)

    def get(self, name: str) -> tuple[ToolMetadata, ToolFunc] | None:
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[ToolMetadata]:
        return [meta for meta, _ in self._tools.values()]


# 模块级单例
default_registry = ToolRegistry()
