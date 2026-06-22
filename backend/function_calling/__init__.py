"""
Function Calling 模块入口

对外暴露：
- default_registry / ToolRegistry         工具注册表
- execute_tool_call / list_tools          编排与列举函数
- ToolCallRequest / ToolCallResult / ToolMetadata / ToolParamField  Pydantic 模型
- FunctionCallError 及其子类              异常体系
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.function_calling.exceptions import (
    FunctionCallError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolTimeoutError,
    ToolValidationError,
)
from backend.function_calling.registry import ToolRegistry, default_registry
from backend.function_calling.sandbox import run_in_sandbox
from backend.function_calling.schemas import (
    ToolCallRequest,
    ToolCallResult,
    ToolMetadata,
    ToolParamField,
)
from backend.function_calling.validator import validate_tool_call

# 触发工具注册：必须在 default_registry 定义之后导入，
# tools 子模块仅依赖 registry + schemas，无循环导入风险
from backend.function_calling import tools  # noqa: F401

logger = logging.getLogger(__name__)

__all__ = [
    "default_registry",
    "ToolRegistry",
    "execute_tool_call",
    "list_tools",
    "ToolCallRequest",
    "ToolCallResult",
    "ToolMetadata",
    "ToolParamField",
    "FunctionCallError",
    "ToolNotFoundError",
    "ToolValidationError",
    "ToolPermissionError",
    "ToolTimeoutError",
    "ToolExecutionError",
]


async def list_tools(user: Any = None) -> list[ToolMetadata]:
    """列出可用工具；非管理员用户过滤掉 requires_admin=True 的工具"""
    all_tools = default_registry.list_tools()
    if getattr(user, "is_admin", False):
        return all_tools
    return [t for t in all_tools if not t.requires_admin]


def _classify_validation_error(exc: FunctionCallError) -> str:
    """校验阶段失败 → 审计状态"""
    if isinstance(exc, ToolPermissionError):
        return "denied"
    if isinstance(exc, ToolNotFoundError):
        return "not_found"
    if isinstance(exc, ToolValidationError):
        return "validation_failed"
    return "failed"


def _classify_execution_error(exc: FunctionCallError) -> str:
    """执行阶段失败 → 审计状态"""
    if isinstance(exc, ToolTimeoutError):
        return "timeout"
    if isinstance(exc, ToolExecutionError):
        return "execution"
    return "failed"


def _serialize_result(result: Any) -> Any:
    """将结果转为可 JSON 序列化结构；失败则存 {"_repr": str(result)[:2000]}"""
    try:
        json.dumps(result, ensure_ascii=False)
        return result
    except (TypeError, ValueError):
        return {"_repr": str(result)[:2000]}


async def _write_audit(
    db: AsyncSession,
    user_id: Optional[int],
    function_name: str,
    params: dict,
    result: Any,
    status: str,
    duration_ms: int,
) -> None:
    """写入 FunctionCallAudit；任何失败都不得影响主调用流程"""
    try:
        from backend.models.audit import FunctionCallAudit  # 延迟导入，避免硬依赖
    except ImportError:
        logger.warning("backend.models.audit 尚未就绪，跳过 Function Call 审计写入")
        return

    try:
        db.add(
            FunctionCallAudit(
                user_id=user_id,
                function_name=function_name,
                params_json=params,
                result_json=_serialize_result(result),
                status=status,
                duration_ms=duration_ms,
            )
        )
        await db.commit()
    except Exception:
        logger.exception("写入 FunctionCallAudit 失败")
        try:
            await db.rollback()
        except Exception:
            pass


async def execute_tool_call(
    db: AsyncSession,
    user: Any,
    request: ToolCallRequest,
    context: Optional[dict] = None,
) -> ToolCallResult:
    """工具调用编排入口：校验 → 沙箱执行 → 审计"""
    ctx = dict(context) if context else {}
    ctx.setdefault("db", db)
    ctx.setdefault("user_id", getattr(user, "id", None))

    start = time.perf_counter()
    error: Optional[str] = None
    result: Any = None
    status = "success"

    # 校验阶段
    try:
        _metadata, func = validate_tool_call(
            default_registry, request.function_name, request.params, user
        )
    except FunctionCallError as e:
        status = _classify_validation_error(e)
        error = str(e)
        duration_ms = int((time.perf_counter() - start) * 1000)
        await _write_audit(
            db, ctx.get("user_id"), request.function_name,
            request.params, None, status, duration_ms,
        )
        return ToolCallResult(
            success=False,
            result=None,
            error=error,
            duration_ms=duration_ms,
            function_name=request.function_name,
        )

    # 执行阶段
    try:
        result = await run_in_sandbox(func, request.params, ctx)
        status = "success"
    except FunctionCallError as e:
        status = _classify_execution_error(e)
        error = str(e)
        result = None

    duration_ms = int((time.perf_counter() - start) * 1000)
    await _write_audit(
        db,
        ctx.get("user_id"),
        request.function_name,
        request.params,
        result,
        status,
        duration_ms,
    )
    return ToolCallResult(
        success=(status == "success"),
        result=result,
        error=error,
        duration_ms=duration_ms,
        function_name=request.function_name,
    )
