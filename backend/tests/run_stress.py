"""压测独立运行脚本，结果写入文件避免终端编码问题"""
import asyncio
import os
import statistics
import time
import uuid

import asyncpg

PG_DSN = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/codesage")
PG_DSN_NATIVE = PG_DSN.replace("postgresql+asyncpg://", "postgresql://")

LINES = []


def log(msg):
    LINES.append(msg)
    print(msg, flush=True)


async def main():
    conn = await asyncpg.connect(PG_DSN_NATIVE)
    try:
        user_id = await conn.fetchval(
            "INSERT INTO users(email, password_hash, email_verified) VALUES ($1,$2,true) RETURNING id",
            f"stress-{uuid.uuid4().hex[:8]}@example.com", "fake-hash",
        )
        session_id = await conn.fetchval(
            "INSERT INTO chat_sessions(user_id, title) VALUES ($1,$2) RETURNING id",
            user_id, "压测会话",
        )

        N = 100_000
        batch = 1000
        rows = []
        base_ts = time.time()
        for i in range(N):
            rows.append((
                uuid.uuid4(), session_id, user_id,
                "user" if i % 2 == 0 else "assistant",
                f"消息内容 #{i} - 一些较长的中文文本用于模拟真实聊天场景 " * 2,
            ))
            if len(rows) == batch:
                await conn.executemany(
                    "INSERT INTO chat_messages(message_id, session_id, user_id, role, content) VALUES ($1,$2,$3,$4,$5)",
                    rows,
                )
                rows.clear()
        if rows:
            await conn.executemany(
                "INSERT INTO chat_messages(message_id, session_id, user_id, role, content) VALUES ($1,$2,$3,$4,$5)",
                rows,
            )
        insert_total = time.time() - base_ts
        log(f"[压测] 写入 {N} 条耗时 {insert_total:.2f}s ({N/insert_total:.0f} rows/s)")

        count = await conn.fetchval("SELECT count(*) FROM chat_messages WHERE user_id=$1", user_id)
        log(f"[压测] 实际行数: {count}")
        assert count == N

        await conn.execute("ANALYZE chat_messages")

        async def timed(sql, args):
            t0 = time.perf_counter()
            rows = await conn.fetch(sql, *args)
            dt = (time.perf_counter() - t0) * 1000
            return dt, len(rows)

        dts1 = []
        for off in (0, 1000, 5000, 50000):
            dt, n = await timed(
                "SELECT * FROM chat_messages WHERE user_id=$1 AND session_id=$2 ORDER BY created_at ASC LIMIT 100 OFFSET $3",
                (user_id, session_id, off),
            )
            dts1.append(dt)
            assert n == 100

        dts2 = []
        for _ in range(20):
            dt, _ = await timed("SELECT count(*) FROM chat_messages WHERE user_id=$1", (user_id,))
            dts2.append(dt)

        sample_mid = await conn.fetchval(
            "SELECT message_id FROM chat_messages WHERE user_id=$1 LIMIT 1 OFFSET 50000", user_id
        )
        dts3 = []
        for _ in range(20):
            dt, n = await timed(
                "SELECT * FROM chat_messages WHERE message_id=$1 AND user_id=$2", (sample_mid, user_id)
            )
            dts3.append(dt)
            assert n == 1

        def report(name, dts):
            p50 = statistics.median(dts)
            p95 = sorted(dts)[int(len(dts) * 0.95) - 1] if len(dts) > 1 else dts[0]
            mx = max(dts)
            log(f"[压测] {name}: P50={p50:.2f}ms P95={p95:.2f}ms MAX={mx:.2f}ms")
            return p95

        p95_1 = report("会话分页查询", dts1)
        p95_2 = report("用户消息计数", dts2)
        p95_3 = report("message_id 点查", dts3)

        ok = p95_1 < 200 and p95_2 < 200 and p95_3 < 200
        log(f"[压测] 结论: {'全部 P95 < 200ms 达标' if ok else '未达标'}")
        return ok
    finally:
        await conn.execute("DELETE FROM chat_messages WHERE user_id=$1", user_id)
        await conn.execute("DELETE FROM chat_sessions WHERE user_id=$1", user_id)
        await conn.execute("DELETE FROM users WHERE id=$1", user_id)
        await conn.close()


if __name__ == "__main__":
    ok = asyncio.run(main())
    with open("backend/tests/stress_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(LINES))
    print("RESULT_FILE=backend/tests/stress_result.txt", flush=True)
    raise SystemExit(0 if ok else 1)
