from typing import Any

from pydantic import BaseModel, Field


class FunctionParamOut(BaseModel):
    name: str
    type: str = "string"
    required: bool = True
    description: str = ""


class FunctionMetaOut(BaseModel):
    name: str
    description: str = ""
    params: list[FunctionParamOut] = Field(default_factory=list)
    requires_admin: bool = False


class FunctionsListOut(BaseModel):
    functions: list[FunctionMetaOut] = Field(default_factory=list)


class FunctionCallIn(BaseModel):
    function_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    target_node_id: str | None = None


class FunctionCallOut(BaseModel):
    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: int = 0
    function_name: str = ""
    node_id: str | None = None
    version_no: int | None = None
