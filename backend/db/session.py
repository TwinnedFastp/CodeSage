from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

# 创建异步数据库引擎
# echo=True 会打印所有 SQL 语句，方便开发调试
engine = create_async_engine(settings.async_database_url, echo=True, future=True)

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
