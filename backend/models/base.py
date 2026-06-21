"""
SQLAlchemy 声明式基类统一入口。

所有模型共享同一个 Base.metadata，便于 init_db 一次性建表与迁移。
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
