"""工具执行软沙箱：超时控制 + 异常归一化"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.function_calling.exceptions import (
    FunctionCallError,
    ToolExecutionError,
    ToolTimeoutError,
)
from backend.function_calling.registry import ToolFunc

logger = logging.getLogger(__name__)


async def run_in_sandbox(
    func: ToolFunc,
    params: dict,
    context: dict,
    timeout: float = 30.0,
) -> Any:
    """
    在软沙箱内执行工具函数：
    - 用 asyncio.wait_for 限制执行时长
    - FunctionCallError 子类（权限/参数/执行类控制流异常）直接透传
    - 其它异常统一归一化为 ToolExecutionError
    真正的进程级隔离不在本期范围，依靠超时 + 异常捕获 + 工具自带限制。
    """
    try:
        return await asyncio.wait_for(func(params, context), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise ToolTimeoutError(f"工具执行超时（>{timeout}s）") from exc
    except FunctionCallError:
        # 权限/参数/工具自行抛出的结构化执行异常：保持原信息透传
        raise
    except Exception as exc:
        raise ToolExecutionError(f"工具执行失败: {exc}") from exc
