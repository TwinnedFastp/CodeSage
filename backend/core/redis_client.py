"""
Redis 客户端与 JWT 令牌管理

职责：
1. 维护 JWT 黑名单（登出后令牌立即失效）
2. 维护刷新令牌白名单（refresh token 必须在 Redis 中存在才允许刷新）
3. 提供登录失败计数缓存（加速锁定判断，DB 仍为最终真相）

Key 设计：
- jwt:blacklist:{jti}        -> "1"   TTL = access 剩余有效期
- jwt:refresh:{user_id}:{jti} -> user_id TTL = refresh 有效期
- login:fail:{email}         -> 失败次数  TTL = 锁定窗口
"""
from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis

from backend.core.config import settings

logger = logging.getLogger(__name__)

# 异步连接池：decode_responses=True 直接拿到 str
_pool: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """获取全局异步 Redis 客户端（惰性单例）。"""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
    return _pool


async def close_redis() -> None:
    """应用关闭时释放连接池。"""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


# ------------------------------------------------------------------
# JWT 黑名单（登出失效）
# ------------------------------------------------------------------
BLACKLIST_PREFIX = "jwt:blacklist:"


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """将 access token 的 jti 加入黑名单，TTL 等于令牌剩余有效期。"""
    if ttl_seconds <= 0:
        return
    client = get_redis()
    await client.set(f"{BLACKLIST_PREFIX}{jti}", "1", ex=ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    """判断某 jti 是否已被吊销。"""
    client = get_redis()
    return bool(await client.get(f"{BLACKLIST_PREFIX}{jti}"))


# ------------------------------------------------------------------
# 刷新令牌白名单
# ------------------------------------------------------------------
REFRESH_PREFIX = "jwt:refresh:"


async def store_refresh_token(user_id: int, jti: str, ttl_seconds: int) -> None:
    """登记一个刷新令牌为有效。"""
    if ttl_seconds <= 0:
        return
    client = get_redis()
    await client.set(f"{REFRESH_PREFIX}{user_id}:{jti}", str(user_id), ex=ttl_seconds)


async def is_refresh_token_valid(user_id: int, jti: str) -> bool:
    """校验刷新令牌是否仍有效（未被登出/未被吊销）。"""
    client = get_redis()
    return bool(await client.get(f"{REFRESH_PREFIX}{user_id}:{jti}"))


async def revoke_refresh_token(user_id: int, jti: str) -> None:
    """吊销某个刷新令牌（登出时调用）。"""
    client = get_redis()
    await client.delete(f"{REFRESH_PREFIX}{user_id}:{jti}")


async def revoke_all_refresh_tokens(user_id: int) -> int:
    """吊销某用户全部刷新令牌（改密/异地登录踢出）。"""
    client = get_redis()
    pattern = f"{REFRESH_PREFIX}{user_id}:*"
    deleted = 0
    async for key in client.scan_iter(match=pattern, count=100):
        await client.delete(key)
        deleted += 1
    return deleted


# ------------------------------------------------------------------
# 登录失败计数（缓存层，加速判断；最终真相在 DB users.locked_until）
# ------------------------------------------------------------------
LOGIN_FAIL_PREFIX = "login:fail:"


async def incr_login_fail(email: str, ttl_seconds: int) -> int:
    """累加失败次数并返回当前值，key 在锁定窗口后自动过期。"""
    client = get_redis()
    key = f"{LOGIN_FAIL_PREFIX}{email.lower()}"
    async with client.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, ttl_seconds)
        result = await pipe.execute()
    return int(result[0])


async def get_login_fail(email: str) -> int:
    client = get_redis()
    val = await client.get(f"{LOGIN_FAIL_PREFIX}{email.lower()}")
    return int(val) if val else 0


async def reset_login_fail(email: str) -> None:
    """登录成功后清空失败计数。"""
    client = get_redis()
    await client.delete(f"{LOGIN_FAIL_PREFIX}{email.lower()}")


# ------------------------------------------------------------------
# Redis Stream 操作（流式对话断点续传）
# ------------------------------------------------------------------
STREAM_PREFIX = "chat:stream:"
STREAM_TTL = 24 * 3600  # 24 小时过期，覆盖长对话 + 异常滞留自动清理
LOCK_PREFIX = "chat:lock:"
LOCK_TTL = 60  # 分布式锁 TTL：略大于大模型最长生成时间（秒）


def _stream_key(session_id: str) -> str:
    """Stream key：每个会话一个 Stream，存储该会话所有流式消息。"""
    return f"{STREAM_PREFIX}{session_id}"


def _lock_key(session_id: str) -> str:
    """分布式锁 key：防止同一 session 重复调用大模型。"""
    return f"{LOCK_PREFIX}{session_id}"


async def stream_add(
    session_id: str,
    data: dict[str, str],
    maxlen: int = 1000,
) -> str | None:
    """
    向指定会话的 Stream 添加一条消息（XADD）。
    返回消息 ID（如 "1719123456789-0"），失败返回 None。
    maxlen 限制 Stream 长度，避免单会话占用过多内存。
    """
    try:
        client = get_redis()
        msg_id = await client.xadd(_stream_key(session_id), data, maxlen=maxlen, approximate=True)
        # 设置/续命 TTL
        await client.expire(_stream_key(session_id), STREAM_TTL)
        return msg_id
    except Exception as exc:
        logger.warning("Stream XADD 失败 session=%s", session_id, exc_info=True)
        return None


async def stream_read_block(
    session_id: str,
    last_id: str = "0",
    count: int = 10,
    block_ms: int = 5000,
) -> list[tuple] | None:
    """
    阻塞读取 Stream 新消息（XREAD BLOCK）。

    从 last_id 之后开始读取，阻塞等待 block_ms 毫秒。
    返回 [(message_id, {field: value}), ...]，超时返回空列表 []，失败返回 None。

    典型用法：
    - 首次连接：last_id="0" 从头读取
    - 断点续传：last_id=上次收到的 message_id
    - 持续监听：循环调用，每次用上一批最后一条的 id 作为 last_id
    """
    try:
        client = get_redis()
        result = await client.xread(
            {_stream_key(session_id): last_id},
            count=count,
            block=block_ms,
        )
        # xread 返回 [[stream_name, [(id, data), ...]], ...]
        if not result:
            return []
        # 取第一个 stream 的消息列表
        return result[0][1] if result and result[0] else []
    except Exception as exc:
        logger.warning("Stream XREAD BLOCK 失败 session=%s last_id=%s", session_id, last_id, exc_info=True)
        return None


async def stream_range(
    session_id: str,
    start: str = "-",
    end: str = "+",
    count: int = 100,
) -> list[tuple]:
    """
    范围读取 Stream 历史消息（XREVRANGE / XRANGE）。
    用于断连恢复时批量获取已产生的全部消息。
    """
    try:
        client = get_redis()
        # xrange 按 ID 正序，xrevrange 按 ID 逆序；这里用 xrange 获取从 start 到 end 的消息
        messages = await client.xrange(_stream_key(session_id), min=start, max=end, count=count)
        return messages
    except Exception as exc:
        logger.warning("Stream XRANGE 失败 session=%s", session_id, exc_info=True)
        return []


async def stream_len(session_id: str) -> int:
    """获取 Stream 消息数量。"""
    try:
        client = get_redis()
        return await client.xlen(_stream_key(session_id))
    except Exception:
        return 0


async def stream_delete(session_id: str) -> int:
    """删除整个 Stream key，释放内存。返回删除的消息数量。"""
    try:
        client = get_redis()
        return await client.delete(_stream_key(session_id))
    except Exception:
        return 0


async def stream_acquire_lock(session_id: str, lock_value: str) -> bool:
    """
    获取分布式锁（SET NX EX）。
    保证同一 session 只发起一次大模型调用。
    返回 True 表示获取成功（可开始生产），False 表示锁已存在（只消费）。
    """
    try:
        client = get_redis()
        acquired = await client.set(_lock_key(session_id), lock_value, nx=True, ex=LOCK_TTL)
        return bool(acquired)
    except Exception as exc:
        logger.warning("Stream 获取分布式锁失败 session=%s", session_id, exc_info=True)
        return False


async def stream_release_lock(session_id: str, lock_value: str) -> bool:
    """释放分布式锁（仅当锁值匹配时才释放，防止误删）。"""
    try:
        client = get_redis()
        # Lua 脚本保证原子性：仅当值匹配时才删除
        lua_script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """
        result = await client.eval(lua_script, 1, _lock_key(session_id), lock_value)
        return bool(result)
    except Exception:
        return False


async def stream_is_locked(session_id: str) -> bool:
    """检查某 session 是否持有活跃的生产锁。"""
    try:
        client = get_redis()
        return bool(await client.exists(_lock_key(session_id)))
    except Exception:
        return False
