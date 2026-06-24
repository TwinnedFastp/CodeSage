"""
流式对话中间状态缓存（Redis Stream）

基于 Redis Stream 实现的生产-消费解耦架构，支持断点续传：

职责：
- 生产端：大模型生成的每个 chunk 通过 XADD 写入 Stream（有序持久化）
- 消费端：通过 XREAD BLOCK 阻塞读取，SSE 推送给前端（支持断点续传）
- 分布式锁：保证同一 session 只发起一次大模型调用（防重复生成）
- 断连恢复：前端刷新后可从任意 message_id 继续接收剩余消息

Key 设计（TTL = 24 小时）：
- chat:stream:{session_id}          -> Stream（存储所有流式消息）
- chat:lock:{session_id}           -> 分布式锁（防止重复生产）

Stream 消息格式（field-value pairs）：
- type:    "start" | "content" | "end" | "error"
- content: 消息正文（chunk 文本或错误信息）
- timestamp: ISO8601 时间戳

与旧版 String APPEND 方案的区别：
- ✅ 支持按游标回溯消费（XREAD 从指定 ID 继续）
- ✅ 阻塞式长轮询（XREAD BLOCK，无消息时挂起等待）
- ✅ 天然有序、天然持久化（AOF/RDB 兜底）
- ✅ 支持多消费者（未来可扩展为 XGROUP 消费组）

调用约定（配合 chat._streaming_with_persistence）：
1. 流式开始：init_streaming -> 获取锁 + 创建 Stream + 写入 start 标记
2. 每个 chunk：append_stream_chunk（XADD 写入 content 消息）
3. 流式结束：write_end_stream（XADD 写入 end 标记）
4. 异常中断：write_error_stream（XADD 写入 error 消息）
5. 前端刷新：get_stream_messages / read_stream_block 恢复
6. 清理：finalize_streaming（释放锁 + 可选删除 Stream）
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from backend.core.redis_client import (
    get_redis,
    stream_add,
    stream_read_block,
    stream_range,
    stream_len,
    stream_delete,
    stream_acquire_lock,
    stream_release_lock,
    stream_is_locked,
)

logger = __name__

# ---- 向后兼容：旧版接口保留（委托到新的 Stream 实现）----

# 旧的 TTL 常量（保持接口兼容）
TTL_SECONDS = 30 * 60


async def init_streaming(
    session_id: str,
    stream_token: Optional[str] = None,
    role: str = "assistant",
    render_mode: str = "text",
) -> str:
    """
    初始化一条流式消息（向后兼容接口）。

    内部行为：
    1. 尝试获取分布式锁（仅首次调用成功）
    2. 写入 start 类型的 Stream 消息
    3. 返回 stream_token 作为标识符
    """
    if stream_token is None:
        stream_token = f"stream_{int(time.time() * 1000)}"

    # 尝试获取生产锁（幂等：已持有则跳过）
    lock_value = f"{session_id}:{stream_token}"
    acquired = await stream_acquire_lock(session_id, lock_value)
    if acquired:
        # 写入 start 标记消息
        meta = json.dumps({
            "role": role,
            "render_mode": render_mode,
            "token": stream_token,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False)
        await stream_add(session_id, {
            "type": "start",
            "content": meta,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("流式缓存初始化成功（获取生产锁）session=%s token=%s", session_id, stream_token)
    else:
        logger.debug("流式缓存初始化：锁已存在，进入纯消费模式 session=%s", session_id)

    return stream_token


async def append_chunk(session_id: str, stream_token: str, chunk: str) -> bool:
    """
    追加一段内容到流式 Stream（向后兼容接口）。
    使用 XADD 原子写入，失败不阻断主流程。
    返回 True 表示写入成功，False 表示失败。
    """
    if not chunk:
        return True
    try:
        msg_id = await stream_add(session_id, {
            "type": "content",
            "content": chunk,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return msg_id is not None
    except Exception as exc:
        logger.warning("Stream 追加 chunk 失败 session=%s token=%s", session_id, stream_token, exc_info=True)
        return False


async def write_end_stream(session_id: str, full_content: str = "") -> bool:
    """
    写入流式结束标记（end 类型消息）。
    无论成功失败都必须调用此方法，避免消费端无限阻塞。
    """
    try:
        msg_id = await stream_add(session_id, {
            "type": "end",
            "content": full_content[:200] if full_content else "",  # 仅存摘要用于调试
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return msg_id is not None
    except Exception as exc:
        logger.warning("Stream 写入 end 标记失败 session=%s", session_id, exc_info=True)
        return False


async def write_error_stream(session_id: str, error_msg: str) -> bool:
    """写入异常错误标记（error 类型消息）。"""
    try:
        msg_id = await stream_add(session_id, {
            "type": "error",
            "content": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return msg_id is not None
    except Exception as exc:
        logger.warning("Stream 写入 error 标记失败 session=%s", session_id, exc_info=True)
        return False


async def get_streaming(session_id: str, stream_token: str) -> Optional[dict]:
    """
    读取单条进行中的流式消息（向后兼容接口）。
    从 Stream 中读取所有 content 类型消息，拼接为完整内容。
    已结束/不存在返回 None。
    """
    messages = await stream_range(session_id)
    if not messages:
        return None

    # 提取元信息（从 start 消息）
    meta = {}
    content_parts = []
    has_end = False
    has_error = False

    for _msg_id, data in messages:
        msg_type = data.get("type", "")
        if msg_type == "start":
            try:
                meta = json.loads(data.get("content", "{}"))
            except (json.JSONDecodeError, TypeError):
                meta = {}
        elif msg_type == "content":
            content_parts.append(data.get("content", ""))
        elif msg_type == "end":
            has_end = True
        elif msg_type == "error":
            has_error = True

    # 如果已有 end 标记且无 error，说明流式已完成（Redis key 可能即将被清理）
    if has_end and not has_error:
        return None

    return {
        "stream_token": stream_token or meta.get("token", ""),
        "content": "".join(content_parts),
        "role": meta.get("role", "assistant"),
        "render_mode": meta.get("render_mode", "text"),
        "started_at": meta.get("started_at"),
    }


async def list_active_streaming(session_id: str) -> list[dict]:
    """
    列出某会话下所有进行中的流式消息（向后兼容接口）。

    检查 Stream 是否存在、是否有活跃内容、是否已被标记为结束。
    返回仍在进行中的消息列表。
    """
    # 快速检查：Stream 是否存在
    count = await stream_len(session_id)
    if count == 0:
        return []

    # 读取全部消息检查状态
    item = await get_streaming(session_id, "")
    if item is None:
        return []

    # 用一个虚拟 token 标识（兼容旧的占位逻辑）
    return [item]


async def finalize_streaming(session_id: str, stream_token: str) -> Optional[str]:
    """
    流式结束清理（向后兼容接口）。

    1. 读取 Stream 全部 content 消息并拼接为完整内容
    2. 释放分布式锁（允许下次重新生成）
    3. 可选：删除 Stream key（默认保留 24h TTL 自动过期）
    返回完整内容供调用方落库 PostgreSQL。
    """
    # 读取全部消息提取内容
    messages = await stream_range(session_id)
    content_parts = []
    for _msg_id, data in messages:
        if data.get("type") == "content":
            content_parts.append(data.get("content", ""))

    full_content = "".join(content_parts)

    # 释放分布式锁
    lock_value = f"{session_id}:{stream_token}" if stream_token else session_id
    await stream_release_lock(session_id, lock_value)

    # 注意：不立即删除 Stream，保留 24h TTL 用于前端恢复查看
    # 如需立即清理可调用 stream_delete(session_id)
    return full_content if full_content else None


# ---- 新增：原生 Stream 操作接口（供断点续传使用）----


async def get_stream_messages(
    session_id: str,
    last_id: str = "0-0",
    count: int = 100,
) -> dict:
    """
    获取 Stream 中的消息（用于断连恢复）。

    参数：
    - last_id: 起始消息 ID，"0-0" 表示从头开始
    - count: 最大返回条数

    返回：
    {
        "messages": [{"msgId": "...", "type": "...", "content": "...", "timestamp": "..."}],
        "lastMsgId": "最后一条消息的 ID",
        "hasMore": True/False,
        "isComplete": True/False  (是否有 end 标记),
        "total": 总消息数,
    }
    """
    messages = await stream_range(session_id, start=last_id, count=count)

    result_msgs = []
    last_msg_id = last_id
    is_complete = False
    has_error = False

    for msg_id, data in messages:
        last_msg_id = msg_id
        msg_type = data.get("type", "")
        result_msgs.append({
            "msgId": msg_id,
            "type": msg_type,
            "content": data.get("content", ""),
            "timestamp": data.get("timestamp", ""),
        })
        if msg_type == "end":
            is_complete = True
        elif msg_type == "error":
            has_error = True

    total = await stream_len(session_id)

    return {
        "messages": result_msgs,
        "lastMsgId": last_msg_id,
        "hasMore": len(messages) >= count,
        "isComplete": is_complete,
        "hasError": has_error,
        "total": total,
    }


async def read_stream_block(
    session_id: str,
    last_id: str = "$",
    count: int = 10,
    block_ms: int = 5000,
) -> dict:
    """
    阻塞读取 Stream 新消息（用于 SSE 断点续传消费端）。

    参数：
    - last_id: 上次读取的最后消息 ID，"$" 表示只读新消息
    - count: 每批最大条数
    - block_ms: 阻塞超时毫秒数（0 = 无限阻塞）

    返回：
    {
        "messages": [...],      # 新消息列表
        "lastMsgId": "...",     # 最后一条消息 ID（下次传入此值继续读）
        "isComplete": bool,     # 是否收到 end 标记
        "hasError": bool,       # 是否收到 error 标记
        "timedOut": bool,       # 是否超时（无新消息）
    }
    """
    # $ 是 Redis Stream 的特殊 ID，表示"尚未传递的消息"
    redis_last_id = last_id if last_id != "0-0" else "0"
    raw_messages = await stream_read_block(session_id, redis_last_id, count=count, block_ms=block_ms)

    if raw_messages is None:
        # Redis 异常
        return {"messages": [], "lastMsgId": last_id, "isComplete": False, "hasError": False, "timedOut": False}

    if len(raw_messages) == 0:
        # 超时无新消息
        return {"messages": [], "lastMsgId": last_id, "isComplete": False, "hasError": False, "timedOut": True}

    result_msgs = []
    last_msg_id = last_id
    is_complete = False
    has_error = False

    for msg_id, data in raw_messages:
        last_msg_id = msg_id
        msg_type = data.get("type", "")
        result_msgs.append({
            "msgId": msg_id,
            "type": msg_type,
            "content": data.get("content", ""),
            "timestamp": data.get("timestamp", ""),
        })
        if msg_type == "end":
            is_complete = True
        elif msg_type == "error":
            has_error = True

    return {
        "messages": result_msgs,
        "lastMsgId": last_msg_id,
        "isComplete": is_complete,
        "hasError": has_error,
        "timedOut": False,
    }


async def is_active(session_id: str, stream_token: str) -> bool:
    """检查某条流式是否仍在进行中（Stream 存在且未被标记为结束）。"""
    # 检查 Stream 是否存在
    if await stream_len(session_id) == 0:
        return False

    # 检查是否有 end 标记
    messages = await stream_range(session_id, count=50)
    for _msg_id, data in messages:
        if data.get("type") == "end":
            return False
    return True


async def check_session_status(session_id: str) -> dict:
    """
    检查会话的流式状态（供前端判断是否需要恢复）。

    返回：
    {
        "isActive": bool,         # 是否仍有活跃的流式生成
        "isLocked": bool,         # 是否持有生产锁（大模型正在生成中）
        "messageCount": int,      # Stream 中的消息总数
        "lockInfo": {             # 锁信息（如果存在）
            "value": str,
            "ttl": float,
        } | None,
    }
    """
    client = get_redis()
    from backend.core.redis_client import _lock_key, _stream_key

    msg_count = await stream_len(session_id)
    locked = await stream_is_locked(session_id)
    lock_info = None

    if locked:
        try:
            lock_key = _lock_key(session_id)
            ttl = await client.ttl(lock_key)
            val = await client.get(lock_key)
            lock_info = {"value": val or "", "ttl": max(0, ttl)}
        except Exception:
            pass

    # 检查是否已完成（有 end 标记）
    completed = False
    if msg_count > 0:
        messages = await stream_range(session_id, count=10)
        for _mid, data in messages:
            if data.get("type") == "end":
                completed = True
                break

    return {
        "isActive": msg_count > 0 and not completed,
        "isLocked": locked,
        "messageCount": msg_count,
        "lockInfo": lock_info,
    }
