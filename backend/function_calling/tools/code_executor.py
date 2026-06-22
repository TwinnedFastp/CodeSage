"""code_executor 工具：在受限软沙箱内执行 Python 代码（仅管理员）"""
from __future__ import annotations

import asyncio
import contextlib
import io
from typing import Any

from backend.function_calling.exceptions import ToolExecutionError
from backend.function_calling.registry import ToolFunc, default_registry
from backend.function_calling.schemas import ToolMetadata, ToolParamField

metadata = ToolMetadata(
    name="code_executor",
    description="在受限沙箱内执行 Python 代码（仅管理员）",
    params=[
        ToolParamField(
            name="code", type="string", required=True, description="待执行的 Python 代码",
        ),
    ],
    requires_admin=True,
)

# 仅放行安全的内置函数；__import__/open/eval/exec/compile/globals 等一律不放行
_ALLOWED_BUILTINS: dict[str, Any] = {
    "print": print,
    "len": len,
    "range": range,
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "sorted": sorted,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "bool": bool,
}

# 沙箱执行超时（秒）
_EXEC_TIMEOUT = 5.0


def _run_restricted(code: str) -> str:
    """在受限 globals 中执行代码，捕获并返回 stdout"""
    buf = io.StringIO()
    restricted_globals: dict[str, Any] = {"__builtins__": _ALLOWED_BUILTINS}
    with contextlib.redirect_stdout(buf):
        exec(code, restricted_globals, {})  # noqa: S102 受控软沙箱内执行
    return buf.getvalue()


async def code_executor(params: dict, context: dict) -> str:
    """在独立线程 + 超时限制下执行受限 Python 代码"""
    code = params["code"]
    try:
        stdout = await asyncio.wait_for(
            asyncio.to_thread(_run_restricted, code), timeout=_EXEC_TIMEOUT,
        )
    except asyncio.TimeoutError as exc:
        raise ToolExecutionError(f"code_executor 执行超时（>{_EXEC_TIMEOUT}s）") from exc
    except Exception as exc:
        raise ToolExecutionError(f"code_executor 执行失败: {exc}") from exc
    return stdout


default_registry.register(metadata, code_executor)
