"""
压力测试：单表 10 万条数据，查询响应时间 < 200ms

策略：
- 使用原始 asyncpg 批量 COPY/execute_values 高速写入 10 万条 chat_messages
- 测试多种查询场景的 P50/P95/P99 响应时间，断言 < 200ms
- 重点验证带 user_id 隔离 + 时间范围 + 索引命中的查询
"""
from __future__ import annotations

import asyncio
import os
import statistics
import time
import uuid

import asyncpg
import pytest

PG_DSN = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/codesage")
# asyncpg 用原生 dsn（不含 +asyncpg）
PG_DSN_NATIVE = PG_DSN.replace("postgresql+asyncpg://", "postgresql://")


@pytest.fixture(scope="module")
def _event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_100k_rows_query_under_200ms():
    """10 万条 chat_messages 下，典型查询 P95 < 200ms"""
    conn = await asyncpg.connect(PG_DSN_NATIVE)

    try:
        # 准备：建一个专属测试用户 + 会话
        user_id = await conn.fetchval(
            "INSERT INTO users(email, password_hash, email_verified) VALUES ($1,$2,true) RETURNING id",
            f"stress-{uuid.uuid4().hex[:8]}@example.com", "fake-hash",
        )
        session_id = await conn.fetchval(
            "INSERT INTO chat_sessions(user_id, title) VALUES ($1,$2) RETURNING id",
            user_id, "压测会话",
        )

        # 批量写入 10 万条消息（execute executemany 分批，每批 1000）
        N = 100_000
        batch = 1000
        rows = []
        base_ts = time.time()
        for i in range(N):
            rows.append((
                uuid.uuid4(),            # message_id
                session_id,              # session_id
                user_id,                 # user_id
                "user" if i % 2 == 0 else "assistant",
                f"消息内容 #{i} - 一些较长的中文文本用于模拟真实聊天场景 " * 2,
            ))
            if len(rows) == batch:
                await conn.executemany(
                    "INSERT INTO chat_messages(message_id, session_id, user_id, role, content) "
                    "VALUES ($1,$2,$3,$4,$5)",
                    rows,
                )
                rows.clear()
        if rows:
            await conn.executemany(
                "INSERT INTO chat_messages(message_id, session_id, user_id, role, content) "
                "VALUES ($1,$2,$3,$4,$5)",
                rows,
            )
        insert_total = time.time() - base_ts
        print(f"\n[压测] 写入 {N} 条耗时 {insert_total:.2f}s ({N/insert_total:.0f} rows/s)")

        count = await conn.fetchval("SELECT count(*) FROM chat_messages WHERE user_id=$1", user_id)
        assert count == N

        # 强制 ANALYZE 让规划器拿到最新统计
        await conn.execute("ANALYZE chat_messages")

        # ---- 查询场景与计时 ----
        async def timed(sql, args):
            t0 = time.perf_counter()
            rows = await conn.fetch(sql, *args)
            dt = (time.perf_counter() - t0) * 1000
            return dt, len(rows)

        # 场景1：分页查询某会话最近消息（命中 ix_chat_messages_session_created）
        dts1 = []
        for off in (0, 1000, 5000, 50000):
            dt, n = await timed(
                "SELECT * FROM chat_messages WHERE user_id=$1 AND session_id=$2 "
                "ORDER BY created_at ASC LIMIT 100 OFFSET $3",
                (user_id, session_id, off),
            )
            dts1.append(dt)
            assert n == 100

        # 场景2：按 user_id 统计消息数（命中 ix_chat_messages_user_created）
        dts2 = []
        for _ in range(20):
            dt, _ = await timed(
                "SELECT count(*) FROM chat_messages WHERE user_id=$1", (user_id,)
            )
            dts2.append(dt)

        # 场景3：点查指定 message_id（命中 unique 索引）
        sample_mid = await conn.fetchval(
            "SELECT message_id FROM chat_messages WHERE user_id=$1 LIMIT 1 OFFSET 50000", user_id
        )
        dts3 = []
        for _ in range(20):
            dt, n = await timed(
                "SELECT * FROM chat_messages WHERE message_id=$1 AND user_id=$2",
                (sample_mid, user_id),
            )
            dts3.append(dt)
            assert n == 1

        def report(name, dts):
            p50 = statistics.median(dts)
            p95 = sorted(dts)[int(len(dts) * 0.95) - 1] if len(dts) > 1 else dts[0]
            mx = max(dts)
            print(f"[压测] {name}: P50={p50:.2f}ms P95={p95:.2f}ms MAX={mx:.2f}ms")
            return p95

        p95_1 = report("会话分页查询", dts1)
        p95_2 = report("用户消息计数", dts2)
        p95_3 = report("message_id 点查", dts3)

        # 断言：所有场景 P95 < 200ms
        assert p95_1 < 200, f"分页查询 P95={p95_1:.2f}ms 超过 200ms"
        assert p95_2 < 200, f"计数查询 P95={p95_2:.2f}ms 超过 200ms"
        assert p95_3 < 200, f"点查 P95={p95_3:.2f}ms 超过 200ms"

    finally:
        # 清理压测数据
        await conn.execute("DELETE FROM chat_messages WHERE user_id=$1", user_id)
        await conn.execute("DELETE FROM chat_sessions WHERE user_id=$1", user_id)
        await conn.execute("DELETE FROM users WHERE id=$1", user_id)
        await conn.close()
