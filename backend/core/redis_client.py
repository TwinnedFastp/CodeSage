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
