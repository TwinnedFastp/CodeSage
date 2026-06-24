"""
流式对话中间状态缓存（Redis）

职责：
- 流式生成过程中，将已接收的内容增量缓存到 Redis，防止客户端断连/刷新导致内容丢失
- 提供会话级"进行中"流式消息查询，供前端刷新后恢复未完成的对话
- 流式正常结束或中断后，由调用方落库 PostgreSQL 并清理 Redis key

Key 设计（TTL = 30 分钟，覆盖正常生成 + 异常滞留自动清理）：
- chat:streaming:content:{session_id}:{stream_token}  -> 已累加的内容（string，APPEND 追加）
- chat:streaming:meta:{session_id}:{stream_token}     -> JSON 元信息（role/started_at/render_mode）
- chat:streaming:index:{session_id}                   -> SET，记录该会话下所有活跃 stream_token

为什么不直接每 chunk 落 PostgreSQL：
- LLM 流式每秒可达 20-50 个 chunk，高频 UPDATE 会造成行锁竞争与 WAL 膨胀
- Redis APPEND 为 O(1)，适合高频追加；PostgreSQL 仅在流式结束时写一次最终态
- Redis 天然 TTL 清理，无需维护过期数据；PostgreSQL 重启不丢最终态，Redis 重启仅丢"进行中"临时态

调用约定（配合 chat._streaming_with_persistence）：
1. 流式开始：init_streaming -> 拿到 stream_token
2. 每个 chunk：append_chunk（失败不阻断主流程，退化为纯内存流）
3. 流式结束/中断：finalize_streaming 拿到完整内容 -> 落库 PG
4. 前端刷新：list_active_streaming 恢复进行中的消息
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.core.redis_client import get_redis

logger = logging.getLogger(__name__)

# Key 前缀
_CONTENT_PREFIX = "chat:streaming:content:"
_META_PREFIX = "chat:streaming:meta:"
_INDEX_PREFIX = "chat:streaming:index:"

# TTL：30 分钟。正常流式几分钟内完成；异常中断后 30 分钟自动清理，避免僵尸 key
TTL_SECONDS = 30 * 60


def _content_key(session_id: str, stream_token: str) -> str:
    return f"{_CONTENT_PREFIX}{session_id}:{stream_token}"


def _meta_key(session_id: str, stream_token: str) -> str:
    return f"{_META_PREFIX}{session_id}:{stream_token}"


def _index_key(session_id: str) -> str:
    return f"{_INDEX_PREFIX}{session_id}"


async def init_streaming(
    session_id: str,
    stream_token: Optional[str] = None,
    role: str = "assistant",
    render_mode: str = "text",
) -> str:
    """
    初始化一条流式消息的缓存。

    生成（或复用）stream_token，写入元信息，登记到会话索引。
    返回 stream_token，后续 append/finalize 都用它定位。
    """
    if stream_token is None:
        stream_token = uuid.uuid4().hex
    client = get_redis()
    meta = {
        "role": role,
        "render_mode": render_mode,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    pipe = client.pipeline()
    pipe.set(_meta_key(session_id, stream_token), json.dumps(meta, ensure_ascii=False), ex=TTL_SECONDS)
    pipe.sadd(_index_key(session_id), stream_token)
    pipe.expire(_index_key(session_id), TTL_SECONDS)
    await pipe.execute()
    return stream_token


async def append_chunk(session_id: str, stream_token: str, chunk: str) -> None:
    """
    追加一段内容到流式缓存。

    使用 APPEND 原子追加，同时续命 TTL（content/meta/index 三 key 同步续命）。
    失败仅记日志，不阻断流式主流程（Redis 不可用时退化为纯内存流，仍能正常落库 PG）。
    """
    if not chunk:
        return
    try:
        client = get_redis()
        key = _content_key(session_id, stream_token)
        pipe = client.pipeline()
        pipe.append(key, chunk)
        pipe.expire(key, TTL_SECONDS)
        # 元信息与索引也续命，避免内容还在但元信息过期导致前端恢复时漏读
        pipe.expire(_meta_key(session_id, stream_token), TTL_SECONDS)
        pipe.expire(_index_key(session_id), TTL_SECONDS)
        await pipe.execute()
    except Exception:
        logger.warning(
            "流式缓存追加失败 session_id=%s token=%s", session_id, stream_token, exc_info=True,
        )


async def get_streaming(session_id: str, stream_token: str) -> Optional[dict]:
    """读取单条进行中的流式消息（内容 + 元信息）。已结束/不存在返回 None。"""
    client = get_redis()
    meta_raw = await client.get(_meta_key(session_id, stream_token))
    if meta_raw is None:
        return None
    content = await client.get(_content_key(session_id, stream_token)) or ""
    try:
        meta = json.loads(meta_raw)
    except json.JSONDecodeError:
        meta = {}
    return {
        "stream_token": stream_token,
        "content": content,
        "role": meta.get("role", "assistant"),
        "render_mode": meta.get("render_mode", "text"),
        "started_at": meta.get("started_at"),
    }


async def list_active_streaming(session_id: str) -> list[dict]:
    """
    列出某会话下所有进行中的流式消息。

    前端刷新页面后调用此接口恢复未完成的对话。流式正常结束后 key 被清理，返回空列表。
    """
    client = get_redis()
    tokens = await client.smembers(_index_key(session_id))
    if not tokens:
        return []
    result = []
    for token in tokens:
        item = await get_streaming(session_id, token)
        if item is not None:
            result.append(item)
    return result


async def finalize_streaming(session_id: str, stream_token: str) -> Optional[str]:
    """
    流式结束：读取最终内容并清理 Redis key。

    返回累加的完整内容（供调用方落库 PostgreSQL）。已清理/不存在返回 None。
    幂等：重复调用不会报错。
    """
    client = get_redis()
    content = await client.get(_content_key(session_id, stream_token))
    pipe = client.pipeline()
    pipe.delete(_content_key(session_id, stream_token))
    pipe.delete(_meta_key(session_id, stream_token))
    pipe.srem(_index_key(session_id), stream_token)
    await pipe.execute()
    return content


async def is_active(session_id: str, stream_token: str) -> bool:
    """检查某条流式是否仍在进行中（元信息 key 存在）。"""
    client = get_redis()
    return bool(await client.exists(_meta_key(session_id, stream_token)))
