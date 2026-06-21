"""
认证全流程功能测试

覆盖场景：
- 注册：邮箱格式错误、密码弱、重复注册、正常注册
- 邮箱验证：无效 token、过期 token、正常验证
- 登录：未验证账号、密码错误、连续5次锁定15分钟、登录成功
- 登出：令牌进黑名单，登出后 /me 失效
- 刷新令牌：刷新成功、旧 refresh 旋转后失效
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from backend.core import redis_client
from backend.models.user import User
from backend.tests.conftest import auth_headers, register_verify_login, unique_email

PASS = "Test@1234"


# ------------------------------------------------------------------
# 注册
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_register_invalid_email_format(client):
    """RFC 不合规邮箱被拦截"""
    for bad in ["not-an-email", "a@b", "@example.com", "user@@example.com", "user@.com"]:
        resp = await client.post("/api/v1/auth/register", json={"email": bad, "password": PASS})
        assert resp.status_code == 422, f"{bad} 应被拒绝，实际 {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_register_weak_password(client):
    """密码复杂度不足被拦截（缺大小写/数字/特殊字符/长度）"""
    cases = ["short", "alllowercase1!", "ALLUPPER1!", "NoDigits!Ab", "NoSpecial1Ab"]
    for bad in cases:
        resp = await client.post("/api/v1/auth/register", json={"email": unique_email(), "password": bad})
        assert resp.status_code == 422, f"密码 {bad} 应被拒绝"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """同一邮箱重复注册被拒"""
    email = unique_email()
    r1 = await client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_register_success_returns_verify_link(client):
    """正常注册成功，开发模式回传验证链接"""
    email = unique_email()
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert resp.status_code == 201
    assert "token=" in resp.json()["detail"]


# ------------------------------------------------------------------
# 邮箱验证
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_verify_email_invalid_token(client):
    resp = await client.post("/api/v1/auth/verify-email", json={"token": "nonexistent-token"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_verify_email_expired(client, db):
    """验证链接过期（>24h）被拒"""
    email = unique_email()
    await client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    # 直接把过期时间改到过去
    await db.execute(
        update(User)
        .where(User.email == email)
        .values(verification_expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
    )
    await db.commit()
    result = await db.execute(select(User).where(User.email == email))
    token = result.scalar_one().verification_token
    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 410  # 过期


@pytest.mark.asyncio
async def test_login_blocked_before_verification(client):
    """未验证邮箱不可登录"""
    email = unique_email()
    await client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PASS})
    assert resp.status_code == 403


# ------------------------------------------------------------------
# 登录锁定
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_wrong_password_then_lockout(client):
    """连续 5 次密码错误后锁定 15 分钟"""
    access, _ = await register_verify_login(client, unique_email())
    # 用一个已验证账号测：直接拿它的邮箱
    from backend.main import app  # noqa
    # 取邮箱：登录拿到 token，从 /me 拿
    me = await client.get("/api/v1/auth/me", headers=auth_headers(access))
    email = me.json()["email"]

    # 前 4 次错误：返回 401，剩余尝试递减
    for i in range(4):
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass!1"})
        assert resp.status_code == 401, f"第{i+1}次应 401"
        assert "剩余尝试" in resp.json()["message"]

    # 第 5 次错误：触发锁定，返回 423
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass!1"})
    assert resp.status_code == 423
    assert "锁定" in resp.json()["message"]

    # 锁定期内即使密码正确也拒绝
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PASS})
    assert resp.status_code == 423


@pytest.mark.asyncio
async def test_login_success_after_lockout_expires(client, db):
    """锁定到期后，正确密码可重新登录"""
    access, _ = await register_verify_login(client, unique_email())
    me = await client.get("/api/v1/auth/me", headers=auth_headers(access))
    email = me.json()["email"]

    # 制造 5 次错误锁定
    for _ in range(5):
        await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass!1"})

    # 把 locked_until 改到过去，模拟到期
    await db.execute(
        update(User).where(User.email == email).values(locked_until=datetime.now(timezone.utc) - timedelta(minutes=1))
    )
    await db.commit()

    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PASS})
    assert resp.status_code == 200


# ------------------------------------------------------------------
# 登录成功 / 当前用户 / 登出 / 刷新
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_full_login_logout_refresh_flow(client):
    email = unique_email()
    access, refresh = await register_verify_login(client, email)

    # /me 可用
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(access))
    assert resp.status_code == 200
    assert resp.json()["email"] == email
    assert resp.json()["email_verified"] is True

    # 刷新令牌
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    new_access = resp.json()["access_token"]
    new_refresh = resp.json()["refresh_token"]
    assert new_access != access and new_refresh != refresh

    # 旧 refresh 旋转后失效
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401

    # 登出
    resp = await client.post("/api/v1/auth/logout", headers=auth_headers(new_access))
    assert resp.status_code == 200

    # 登出后 access 进黑名单，/me 失效
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(new_access))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_records_ip(client, db):
    """登录成功后 IP 被加密记录"""
    email = unique_email()
    access, _ = await register_verify_login(client, email)
    me = await client.get("/api/v1/auth/me", headers=auth_headers(access))
    result = await db.execute(select(User).where(User.email == me.json()["email"]))
    user = result.scalar_one()
    # last_login_ip 应为加密密文（带 enc:: 前缀），不是明文 testserver
    assert user.last_login_ip is not None
    assert user.last_login_ip.startswith("enc::")
    assert "testserver" not in user.last_login_ip


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    """无效令牌访问 /me 被拒"""
    resp = await client.get("/api/v1/auth/me", headers=auth_headers("invalid.token.here"))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_no_token_rejected(client):
    """无令牌访问 /me 被拒"""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
