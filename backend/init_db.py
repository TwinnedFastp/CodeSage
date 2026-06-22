"""
数据库初始化脚本：创建全部表与索引。

用法：
    python -m backend.init_db            # 容器内 / 项目根
    python backend/init_db.py            # 直接运行

幂等：使用 create_all，已存在的表不会被重建。
如需重建结构，请使用 Alembic 迁移，不要在生产环境 drop。
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from backend.db.session import engine
# 导入全部模型，触发 Base.metadata 注册
from backend.models import Base, User, LoginLog, ChatSession, ChatMessage, UserPreference, UserFact, UserTask, AIProvider, UiNode, UiNodeVersion, UiNodeRelation, FunctionCallAudit  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("init_db")


async def init_db() -> None:
    """创建所有表与索引。"""
    async with engine.begin() as conn:
        # gen_random_uuid() 依赖 pgcrypto 扩展（PG13+ 内置 pgcrypto 不再必需，
        # 但显式启用保证兼容性）
        logger.info("启用 pgcrypto 扩展（gen_random_uuid 依赖）...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        logger.info("开始创建表结构...")
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1024)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_object_key VARCHAR(512)"))
        await conn.execute(text("UPDATE users SET username = split_part(email, '@', 1) WHERE username IS NULL OR username = ''"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN username SET NOT NULL"))
        logger.info("表结构创建完成（已存在的表跳过）")


async def main() -> None:
    logger.info("=== CodeSage 数据库初始化开始 ===")
    try:
        await init_db()
        logger.info("=== 初始化成功 ===")
    except Exception:
        logger.exception("=== 初始化失败 ===")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
