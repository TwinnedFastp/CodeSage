"""
pytest 共享 fixtures

测试连接：
- 数据库：localhost:5432/codesage（直连 Docker 暴露的 PG）
- Redis：localhost:6379/0（直连 Docker 暴露的 Redis）

每个测试函数独立事务 + 结尾回滚，保证用例隔离、不污染数据。
测试前会清空 Redis db0，避免黑名单/refresh 残留。
"""
from __future__ import annotations

import asyncio
import os
import uuid

# ---- 强制测试环境变量（在导入 backend 之前设置）----
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/codesage")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod-32bytes")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core import redis_client
from backend.db.session import AsyncSessionLocal, engine
from backend.main import app
from backend.models.base import Base  # noqa: F401  (ensure registry)
# 触发模型注册
from backend.models import (  # noqa: F401
    ChatMessage, ChatSession, LoginLog, User, UserFact, UserPreference, UserTask,
)


@pytest_asyncio.fixture(autouse=True)
async def _clean_db_and_redis():
    """每个测试前后：重置 Redis 连接池 + 清空 db0 + 按表清空 DB（保证隔离）。

    Redis 异步连接绑定事件循环，pytest-asyncio auto 模式每个测试用独立循环，
    因此每轮需重建连接池，避免 'Event loop is closed'。
    """
    # 重建 Redis 连接池（绑定当前测试的事件循环）
    await redis_client.close_redis()

    # 清 Redis
    r = redis_client.get_redis()
    await r.flushdb()

    yield

    # 关闭本轮 Redis 连接，避免污染下一个测试的循环
    try:
        await r.aclose()
    except Exception:
        pass
    await redis_client.close_redis()

    # 测试后清表，避免跨用例污染
    async with engine.begin() as conn:
        for table in (
            "user_tasks", "user_facts", "user_preferences",
            "chat_messages", "chat_sessions", "login_logs", "users",
        ):
            await conn.exec_driver_sql(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE')


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ------------------------------------------------------------------
# 业务辅助：注册 + 验证 + 登录，返回 (user_id, access_token, refresh_token)
# ------------------------------------------------------------------
async def register_verify_login(
    client: AsyncClient, email: str, password: str = "Test@1234",
) -> tuple[int, str, str]:
    # 注册
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    # 开发模式回传验证链接，从中提取 token
    detail = resp.json().get("detail", "")
    token = detail.split("token=")[-1] if "token=" in detail else ""
    assert token, f"未取到验证 token: {detail}"
    # 验证邮箱
    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200, resp.text
    # 登录
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data["access_token"], data["refresh_token"]


def auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def unique_email() -> str:
    return f"user{uuid.uuid4().hex[:8]}@example.com"
