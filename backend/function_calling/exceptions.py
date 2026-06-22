"""Function Calling 模块异常体系"""
from __future__ import annotations


class FunctionCallError(Exception):
    """Function Calling 模块异常基类，带 message + status 属性"""

    def __init__(self, message: str = "", status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class ToolNotFoundError(FunctionCallError):
    """请求的工具未注册"""

    def __init__(self, message: str = "工具未找到") -> None:
        super().__init__(message, status=404)


class ToolValidationError(FunctionCallError):
    """工具参数校验失败"""

    def __init__(self, message: str = "工具参数校验失败") -> None:
        super().__init__(message, status=422)


class ToolPermissionError(FunctionCallError):
    """调用方无权调用该工具（如缺少管理员权限）"""

    def __init__(self, message: str = "无权限调用该工具") -> None:
        super().__init__(message, status=403)


class ToolTimeoutError(FunctionCallError):
    """工具执行超时"""

    def __init__(self, message: str = "工具执行超时") -> None:
        super().__init__(message, status=504)


class ToolExecutionError(FunctionCallError):
    """工具执行过程中发生异常"""

    def __init__(self, message: str = "工具执行失败") -> None:
        super().__init__(message, status=500)
