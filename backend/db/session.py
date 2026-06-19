from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

# 创建异步数据库引擎
# echo=False：生产环境不打印全部 SQL（避免日志泄漏与性能损耗），调试时可在 .env 临时改 True
engine = create_async_engine(settings.async_database_url, echo=False, future=True, pool_pre_ping=True)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 依赖注入函数：获取数据库连接
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
