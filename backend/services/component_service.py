"""
组件协议生成服务

封装 LLM 调用，按 COMPONENT_PROTOCOL_PROMPT 输出 ComponentProtocol：
- generate_component_protocol: 非流式生成并解析为 ComponentProtocol
- stream_component_protocol_raw: 流式产出原始文本片段，由调用方累积后解析

支持 UI 设计工具（function calling），AI 可调用 draw_beautiful_page 等工具生成精美网页。
"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.function_calling.registry import default_registry
from backend.schemas.component import ComponentProtocol, component_protocol_from_text
from backend.services.provider_service import resolve_provider_config
from backend.sys_prompts import COMPONENT_PROTOCOL_PROMPT

logger = logging.getLogger(__name__)

# UI 设计工具名称白名单 — 只把这些工具注入给组件生成流程
UI_TOOL_NAMES = {
    "draw_ui_page",
    "draw_landing_page",
    "draw_dashboard",
    "draw_portfolio",
    "draw_beautiful_page",
    "generate_design_system",
}


def _get_ui_tools_for_openai() -> list[dict]:
    """将 registry 中的 UI 工具转换为 OpenAI tools 格式"""
    all_tools = default_registry.list_tools()
    ui_tools = [t for t in all_tools if t.name in UI_TOOL_NAMES]

    openai_tools = []
    for tool in ui_tools:
        properties = {}
        required = []
        for param in tool.params:
            prop_def: dict[str, Any] = {
                "type": _map_type_to_openai(param.type),
                "description": param.description,
            }
            if param.type == "array":
                prop_def["items"] = {"type": "string"}
            properties[param.name] = prop_def
            if param.required:
                required.append(param.name)

        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        })
    return openai_tools


def _map_type_to_openai(type_str: str) -> str:
    """映射自定义类型到 OpenAI JSON Schema 类型"""
    mapping = {
        "string": "string",
        "int": "integer",
        "bool": "boolean",
        "object": "object",
        "array": "array",
        "number": "number",
    }
    return mapping.get(type_str, "string")


def _build_messages(
    history_messages: list[dict], instruction: str, context_text: str
) -> list[dict]:
    """组装 system + 历史 + 当前指令的消息序列。"""
    system_prompt = COMPONENT_PROTOCOL_PROMPT + (
        "\n\n【上下文信息】\n" + context_text if context_text else ""
    )
    return (
        [{"role": "system", "content": system_prompt}]
        + list(history_messages)
        + [{"role": "user", "content": instruction}]
    )


async def _resolve_client(db: AsyncSession, user_id: int):
    """解析供应商配置并构造 AsyncOpenAI 客户端，未配置时抛 RuntimeError。"""
    cfg = await resolve_provider_config(db, user_id)
    if not cfg:
        raise RuntimeError("未配置 AI 供应商，请在设置页添加供应商配置")
    client = AsyncOpenAI(api_key=cfg["llm_api_key"], base_url=cfg["llm_base_url"])
    return cfg, client


async def _execute_tool_call(tool_name: str, tool_args: dict) -> dict:
    """执行工具调用并返回结果"""
    entry = default_registry.get(tool_name)
    if not entry:
        logger.warning("工具 %s 未注册", tool_name)
        return {"success": False, "error": f"工具 {tool_name} 不存在"}

    meta, func = entry
    try:
        result = await func(tool_args, context={})
        if isinstance(result, dict):
            return result
        return {"success": True, "result": result}
    except Exception as e:
        logger.exception("工具执行失败: %s", tool_name)
        return {"success": False, "error": str(e)}


async def generate_component_protocol(
    db: AsyncSession,
    user_id: int,
    history_messages: list[dict],
    instruction: str,
    context_text: str = "",
) -> ComponentProtocol:
    """非流式生成组件协议，返回经白名单校验的 ComponentProtocol。

    支持 function calling：当 AI 调用 UI 设计工具时，自动执行并将结果注入响应。
    """
    cfg, client = await _resolve_client(db, user_id)
    from backend.services import memory_service

    context_text = await memory_service.build_generation_context(
        db,
        user_id,
        instruction,
        context_text,
        provider_config=cfg,
    )
    messages = _build_messages(history_messages, instruction, context_text)
    tools = _get_ui_tools_for_openai()

    resp = await client.chat.completions.create(
        model=cfg["llm_model"],
        messages=messages,
        temperature=0.65,
        stream=False,
        tools=tools if tools else None,  # 注入 UI 工具
        tool_choice="auto",  # 让 AI 自主决定是否使用工具
    )

    choice = resp.choices[0]
    message = choice.message

    # 处理工具调用
    if message.tool_calls:
        messages.append(message.model_dump())  # 添加 assistant 的工具调用消息

        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                fn_args = {}

            logger.info("AI 调用 UI 工具: %s(%s)", fn_name, list(fn_args.keys()))

            # 执行工具
            result = await _execute_tool_call(fn_name, fn_args)

            # 将工具结果加入对话
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        # 让 AI 基于工具结果继续输出组件协议
        resp2 = await client.chat.completions.create(
            model=cfg["llm_model"],
            messages=messages,
            temperature=0.65,
            stream=False,
        )
        raw = resp2.choices[0].message.content or ""
    else:
        raw = message.content or ""

    return component_protocol_from_text(raw)


async def stream_component_protocol_raw(
    db: AsyncSession,
    user_id: int,
    history_messages: list[dict],
    instruction: str,
    context_text: str = "",
) -> AsyncIterator[str]:
    """流式产出模型原始文本片段；调用方累积后在结尾统一解析为 ComponentProtocol。

    注意：流式模式下不处理 function calling（OpenAI 流式 tool_calls 较复杂）。
    如需工具能力请使用非流式的 generate_component_protocol。
    """
    cfg, client = await _resolve_client(db, user_id)
    from backend.services import memory_service

    context_text = await memory_service.build_generation_context(
        db,
        user_id,
        instruction,
        context_text,
        provider_config=cfg,
    )
    messages = _build_messages(history_messages, instruction, context_text)

    try:
        stream = await client.chat.completions.create(
            model=cfg["llm_model"],
            messages=messages,
            temperature=0.65,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                piece = delta.content or getattr(delta, "reasoning_content", None)
                if piece:
                    yield piece
    except Exception:
        logger.exception("流式生成组件协议失败 user_id=%s", user_id)
