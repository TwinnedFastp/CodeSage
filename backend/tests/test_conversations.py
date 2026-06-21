"""
LLM 会话存储功能测试

覆盖：
- 原始聊天记录：写入、查询、更新（会话摘要）
- 会话摘要、用户长期偏好、重要事实记忆、任务状态 的 CRUD
- 多用户数据隔离：用户 B 无法访问/操作用户 A 的数据
- 敏感字段加密：user_facts.fact_value 落库为密文，读取为明文
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from backend.models.conversation import ChatMessage, UserFact
from backend.tests.conftest import auth_headers, register_verify_login, unique_email
from backend.utils.crypto import decrypt

PASS = "Test@1234"


async def _two_users(client):
    """创建两个独立用户，返回 (tokenA, tokenB)"""
    a, _ = await register_verify_login(client, unique_email())
    b, _ = await register_verify_login(client, unique_email())
    return a, b


# ------------------------------------------------------------------
# 会话 + 消息
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_session_and_messages_crud(client):
    access, _ = await register_verify_login(client, unique_email())
    H = auth_headers(access)

    # 创建会话
    r = await client.post("/api/v1/conversations/sessions", json={"title": "测试会话"}, headers=H)
    assert r.status_code == 201
    session = r.json()
    sid = session["id"]
    assert session["title"] == "测试会话"

    # 写入消息（user + assistant 各一条）
    r = await client.post("/api/v1/conversations/messages",
                          json={"session_id": sid, "role": "user", "content": "你好"}, headers=H)
    assert r.status_code == 201
    r = await client.post("/api/v1/conversations/messages",
                          json={"session_id": sid, "role": "assistant", "content": "你好，有什么可以帮你？"}, headers=H)
    assert r.status_code == 201

    # 查询消息（按时间正序）
    r = await client.get(f"/api/v1/conversations/sessions/{sid}/messages", headers=H)
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert msgs[0]["content"] == "你好"

    # 更新会话摘要
    r = await client.patch(f"/api/v1/conversations/sessions/{sid}",
                           json={"summary": "用户打招呼，助手回应"}, headers=H)
    assert r.status_code == 200
    assert r.json()["summary"] == "用户打招呼，助手回应"
    assert r.json()["summary_generated_at"] is not None

    # 列出会话
    r = await client.get("/api/v1/conversations/sessions", headers=H)
    assert r.status_code == 200
    assert len(r.json()) == 1

    # 删除会话（级联删消息）
    r = await client.delete(f"/api/v1/conversations/sessions/{sid}", headers=H)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/conversations/sessions/{sid}", headers=H)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_message_invalid_role_rejected(client):
    access, _ = await register_verify_login(client, unique_email())
    H = auth_headers(access)
    r = await client.post("/api/v1/conversations/sessions", json={"title": "x"}, headers=H)
    sid = r.json()["id"]
    r = await client.post("/api/v1/conversations/messages",
                          json={"session_id": sid, "role": "admin", "content": "x"}, headers=H)
    assert r.status_code == 422  # role 不合法


# ------------------------------------------------------------------
# 用户偏好（JSONB 合并）
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_preferences_merge_and_get(client):
    access, _ = await register_verify_login(client, unique_email())
    H = auth_headers(access)

    # 首次 GET：空
    r = await client.get("/api/v1/conversations/preferences", headers=H)
    assert r.status_code == 200
    assert r.json()["preferences"] == {}

    # 写入部分
    r = await client.put("/api/v1/conversations/preferences",
                         json={"preferences": {"language": "zh", "theme": "dark"}}, headers=H)
    assert r.status_code == 200
    assert r.json()["preferences"] == {"language": "zh", "theme": "dark"}

    # 合并更新：theme 覆盖，新增 tone
    r = await client.put("/api/v1/conversations/preferences",
                         json={"preferences": {"theme": "light", "tone": "concise"}}, headers=H)
    assert r.status_code == 200
    prefs = r.json()["preferences"]
    assert prefs == {"language": "zh", "theme": "light", "tone": "concise"}


# ------------------------------------------------------------------
# 重要事实记忆（加密 + CRUD）
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fact_encrypt_at_rest_and_crud(client, db):
    access, _ = await register_verify_login(client, unique_email())
    H = auth_headers(access)
    me = await client.get("/api/v1/auth/me", headers=H)
    user_id = me.json()["id"]

    secret_value = "身份证号:110101199001011234"
    r = await client.post("/api/v1/conversations/facts",
                          json={"fact_key": "id_card", "fact_value": secret_value,
                                "fact_category": "profile"}, headers=H)
    assert r.status_code == 201

    # 直接查库验证加密：落库应为密文，不是明文
    result = await db.execute(select(UserFact).where(UserFact.user_id == user_id, UserFact.fact_key == "id_card"))
    fact_row = result.scalar_one()
    assert fact_row.fact_value != secret_value
    assert fact_row.fact_value.startswith("enc::")
    assert decrypt(fact_row.fact_value) == secret_value

    # 通过 API 读取返回明文
    r = await client.get("/api/v1/conversations/facts", headers=H)
    assert r.status_code == 200
    facts = r.json()
    assert len(facts) == 1
    assert facts[0]["fact_value"] == secret_value  # 接口返回明文

    # upsert 同 key 覆盖
    r = await client.post("/api/v1/conversations/facts",
                          json={"fact_key": "id_card", "fact_value": "新值", "fact_category": "profile"}, headers=H)
    assert r.status_code == 201
    r = await client.get("/api/v1/conversations/facts", headers=H)
    assert len(r.json()) == 1
    assert r.json()[0]["fact_value"] == "新值"

    # 按分类查询
    await client.post("/api/v1/conversations/facts",
                      json={"fact_key": "addr", "fact_value": "北京", "fact_category": "address"}, headers=H)
    r = await client.get("/api/v1/conversations/facts?category=address", headers=H)
    assert len(r.json()) == 1
    assert r.json()[0]["fact_key"] == "addr"

    # 删除
    fact_id = r.json()[0]["id"]
    r = await client.delete(f"/api/v1/conversations/facts/{fact_id}", headers=H)
    assert r.status_code == 204


# ------------------------------------------------------------------
# 任务状态流转
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_task_status_flow(client):
    access, _ = await register_verify_login(client, unique_email())
    H = auth_headers(access)

    # 创建任务 pending
    r = await client.post("/api/v1/conversations/tasks",
                          json={"title": "写报告", "description": "周报", "status": "pending"}, headers=H)
    assert r.status_code == 201
    task = r.json()
    assert task["status"] == "pending"
    tid = task["id"]

    # 流转：pending -> in_progress -> completed
    r = await client.patch(f"/api/v1/conversations/tasks/{tid}", json={"status": "in_progress"}, headers=H)
    assert r.json()["status"] == "in_progress"
    r = await client.patch(f"/api/v1/conversations/tasks/{tid}", json={"status": "completed"}, headers=H)
    assert r.json()["status"] == "completed"

    # 按状态过滤
    r = await client.get("/api/v1/conversations/tasks?status=completed", headers=H)
    assert len(r.json()) == 1
    r = await client.get("/api/v1/conversations/tasks?status=pending", headers=H)
    assert len(r.json()) == 0

    # 非法状态被拒
    r = await client.patch(f"/api/v1/conversations/tasks/{tid}", json={"status": "invalid"}, headers=H)
    assert r.status_code == 422


# ------------------------------------------------------------------
# 多用户数据隔离
# ------------------------------------------------------------------
@pytest.mark.asyncio
async def test_session_isolation_between_users(client):
    """用户 A 的会话，用户 B 不可见/不可操作"""
    a, b = await _two_users(client)
    Ha, Hb = auth_headers(a), auth_headers(b)

    # A 创建会话 + 消息
    r = await client.post("/api/v1/conversations/sessions", json={"title": "A的会话"}, headers=Ha)
    sid = r.json()["id"]
    await client.post("/api/v1/conversations/messages",
                      json={"session_id": sid, "role": "user", "content": "A的机密"}, headers=Ha)

    # B 列表看不到 A 的会话
    r = await client.get("/api/v1/conversations/sessions", headers=Hb)
    assert r.json() == []

    # B 直接访问 A 的会话 -> 404
    r = await client.get(f"/api/v1/conversations/sessions/{sid}", headers=Hb)
    assert r.status_code == 404
    # B 读 A 的消息 -> 404
    r = await client.get(f"/api/v1/conversations/sessions/{sid}/messages", headers=Hb)
    assert r.status_code == 404
    # B 往 A 的会话写消息 -> 404
    r = await client.post("/api/v1/conversations/messages",
                          json={"session_id": sid, "role": "user", "content": "注入"}, headers=Hb)
    assert r.status_code == 404
    # B 删除 A 的会话 -> 404
    r = await client.delete(f"/api/v1/conversations/sessions/{sid}", headers=Hb)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_fact_isolation_between_users(client):
    a, b = await _two_users(client)
    Ha, Hb = auth_headers(a), auth_headers(b)

    # A 写事实
    await client.post("/api/v1/conversations/facts",
                      json={"fact_key": "secret", "fact_value": "A的秘密", "fact_category": "p"}, headers=Ha)
    # B 用同 key 写自己的事实（不应冲突，因为是不同 user_id）
    r = await client.post("/api/v1/conversations/facts",
                          json={"fact_key": "secret", "fact_value": "B的秘密", "fact_category": "p"}, headers=Hb)
    assert r.status_code == 201

    # 各自只能看到自己的
    r = await client.get("/api/v1/conversations/facts", headers=Ha)
    assert r.json()[0]["fact_value"] == "A的秘密"
    r = await client.get("/api/v1/conversations/facts", headers=Hb)
    assert r.json()[0]["fact_value"] == "B的秘密"


@pytest.mark.asyncio
async def test_task_isolation_between_users(client):
    a, b = await _two_users(client)
    Ha, Hb = auth_headers(a), auth_headers(b)

    r = await client.post("/api/v1/conversations/tasks", json={"title": "A的任务"}, headers=Ha)
    tid = r.json()["id"]

    # B 列表看不到
    assert (await client.get("/api/v1/conversations/tasks", headers=Hb)).json() == []
    # B 修改 A 的任务 -> 404
    r = await client.patch(f"/api/v1/conversations/tasks/{tid}", json={"status": "completed"}, headers=Hb)
    assert r.status_code == 404
    # B 删除 A 的任务 -> 404
    r = await client.delete(f"/api/v1/conversations/tasks/{tid}", headers=Hb)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_preference_isolation_between_users(client):
    a, b = await _two_users(client)
    Ha, Hb = auth_headers(a), auth_headers(b)

    await client.put("/api/v1/conversations/preferences", json={"preferences": {"lang": "zh"}}, headers=Ha)
    await client.put("/api/v1/conversations/preferences", json={"preferences": {"lang": "en"}}, headers=Hb)

    assert (await client.get("/api/v1/conversations/preferences", headers=Ha)).json()["preferences"] == {"lang": "zh"}
    assert (await client.get("/api/v1/conversations/preferences", headers=Hb)).json()["preferences"] == {"lang": "en"}
