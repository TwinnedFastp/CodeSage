"""
组件协议生成服务

封装 LLM 调用，按 COMPONENT_PROTOCOL_PROMPT 输出 ComponentProtocol：
- generate_component_protocol: 非流式生成并解析为 ComponentProtocol
- stream_component_protocol_raw: 流式产出原始文本片段，由调用方累积后解析
"""
from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.component import ComponentProtocol, component_protocol_from_text
from backend.services.provider_service import resolve_provider_config
from backend.sys_prompts import COMPONENT_PROTOCOL_PROMPT

logger = logging.getLogger(__name__)


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


async def generate_component_protocol(
    db: AsyncSession,
    user_id: int,
    history_messages: list[dict],
    instruction: str,
    context_text: str = "",
) -> ComponentProtocol:
    """非流式生成组件协议，返回经白名单校验的 ComponentProtocol。"""
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

    resp = await client.chat.completions.create(
        model=cfg["llm_model"],
        messages=messages,
        temperature=0.65,
        stream=False,
    )
    raw = resp.choices[0].message.content or ""
    return component_protocol_from_text(raw)


async def stream_component_protocol_raw(
    db: AsyncSession,
    user_id: int,
    history_messages: list[dict],
    instruction: str,
    context_text: str = "",
) -> AsyncIterator[str]:
    """流式产出模型原始文本片段；调用方累积后在结尾统一解析为 ComponentProtocol。"""
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
