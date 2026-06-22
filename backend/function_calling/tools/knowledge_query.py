"""knowledge_query 工具：检索 CodeSage 知识库（LightRAG）"""
from __future__ import annotations

from backend.function_calling.exceptions import ToolExecutionError
from backend.function_calling.registry import ToolFunc, default_registry
from backend.function_calling.schemas import ToolMetadata, ToolParamField

metadata = ToolMetadata(
    name="knowledge_query",
    description="检索 CodeSage 知识库（LightRAG）",
    params=[
        ToolParamField(
            name="query", type="string", required=True, description="检索问题",
        ),
        ToolParamField(
            name="mode", type="string", required=False,
            description="naive/local/global/hybrid，默认 hybrid",
        ),
    ],
    requires_admin=False,
)


async def knowledge_query(params: dict, context: dict) -> str:
    """根据 query/mode 调用 LightRAG 检索知识库"""
    user_id = context.get("user_id")
    provider_config = context.get("provider_config")
    if user_id is None or not provider_config:
        raise ToolExecutionError("knowledge_query 缺少上下文 user_id/provider_config")

    # 延迟导入：避免模块导入阶段强依赖 rag/config 链，保证注册表可独立加载
    from backend.rag.service import lightrag_service

    query = params["query"]
    mode = params.get("mode", "hybrid")
    return await lightrag_service.query(user_id, provider_config, query, mode=mode)


default_registry.register(metadata, knowledge_query)
