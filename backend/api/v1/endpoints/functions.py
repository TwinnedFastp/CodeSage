from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.function_calling import ToolCallRequest, execute_tool_call, list_tools
from backend.models.user import User
from backend.schemas.function_calling import FunctionCallIn, FunctionCallOut, FunctionsListOut
from backend.services.node_service import append_tool_result_version
from backend.services.provider_service import resolve_provider_config

router = APIRouter()


@router.get("/list", response_model=FunctionsListOut)
async def list_functions(user: User = Depends(get_current_user)):
    tools = await list_tools(user)
    return {"functions": [metadata.model_dump() for metadata in tools]}


@router.post("/call", response_model=FunctionCallOut)
async def call_function(
    payload: FunctionCallIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    provider_config = await resolve_provider_config(db, user.id)
    request = ToolCallRequest(
        function_name=payload.function_name,
        params=payload.params,
        target_node_id=payload.target_node_id,
    )
    result = await execute_tool_call(
        db, user, request, context={"provider_config": provider_config}
    )
    response = result.model_dump(mode="json")

    if payload.target_node_id and result.success:
        try:
            node, version = await append_tool_result_version(
                db, user.id, payload.target_node_id, payload.function_name, result.result
            )
            response["node_id"] = str(node.id)
            response["version_no"] = version.version_no
        except Exception as exc:
            response["success"] = False
            response["error"] = f"工具调用成功，但节点更新失败：{exc}"
            response["node_id"] = payload.target_node_id

    return response
