from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.conversation import UserFact, UserPreference
from backend.utils.crypto import decrypt


_MEMORY_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    lowered = (text or "").lower()
    words = {token for token in _MEMORY_TOKEN_RE.findall(lowered) if token.strip()}
    chars = {char for char in lowered if "\u4e00" <= char <= "\u9fff"}
    return words | chars


def _flatten_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items: list[str] = []
        for key, item in value.items():
            nested = _flatten_value(item)
            if nested:
                items.extend(f"{key}: {part}" for part in nested)
            else:
                items.append(str(key))
        return items
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_flatten_value(item))
        return items
    text = str(value).strip()
    return [text] if text else []


def _score(query_tokens: set[str], text: str) -> int:
    if not query_tokens:
        return 0
    memory_tokens = _tokens(text)
    return len(query_tokens & memory_tokens)


async def _build_embedding(text: str, provider_config: dict | None = None) -> list[float] | None:
    if not text.strip() or not provider_config:
        return None
    api_key = provider_config.get("llm_api_key")
    model = provider_config.get("embedding_model")
    if not api_key or not model:
        return None
    client = AsyncOpenAI(api_key=api_key, base_url=provider_config.get("llm_base_url"))
    response = await client.embeddings.create(model=model, input=text)
    if not response.data:
        return None
    return response.data[0].embedding


async def recall_long_term_memory(
    db: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 8,
    provider_config: dict | None = None,
) -> str:
    safe_limit = max(1, min(limit, 20))
    fact_limit = max(safe_limit * 3, 12)

    preference_result = await db.execute(
        select(UserPreference)
        .where(UserPreference.user_id == user_id)
        .order_by(UserPreference.updated_at.desc(), UserPreference.created_at.desc())
        .limit(4)
    )
    fact_result = await db.execute(
        select(UserFact)
        .where(UserFact.user_id == user_id)
        .order_by(UserFact.updated_at.desc(), UserFact.created_at.desc())
        .limit(fact_limit)
    )

    candidates: list[tuple[str, str]] = []
    for preference in preference_result.scalars().all():
        for item in _flatten_value(preference.preferences):
            candidates.append(("偏好", item))

    for fact in fact_result.scalars().all():
        value = decrypt(fact.fact_value) or ""
        value = value.strip()
        if not value:
            continue
        key = fact.fact_key.strip() if fact.fact_key else "事实"
        category = f"{fact.fact_category.strip()} / " if fact.fact_category else ""
        candidates.append(("事实", f"{category}{key}: {value}"))

    if not candidates:
        return ""

    query_tokens = _tokens(query)
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (_score(query_tokens, item[1][1]), -item[0]),
        reverse=True,
    )
    selected = [candidates[index] for index, _ in ranked[:safe_limit]]
    lines = ["【长期记忆】"]
    lines.extend(f"- {kind}：{text}" for kind, text in selected if text.strip())
    return "\n".join(lines) if len(lines) > 1 else ""


async def build_generation_context(
    db: AsyncSession,
    user_id: int,
    instruction: str,
    base_context: str = "",
    provider_config: dict | None = None,
) -> str:
    long_term_memory = await recall_long_term_memory(
        db=db,
        user_id=user_id,
        query=instruction,
        provider_config=provider_config,
    )
    if base_context and long_term_memory:
        return base_context + "\n\n" + long_term_memory
    return base_context or long_term_memory
