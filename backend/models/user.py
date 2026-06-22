"""
用户与认证相关数据模型

表：
- users         邮箱用户（含邮箱验证、登录锁定、上次登录 IP 等安全字段）
- login_logs    登录审计日志（成功/失败、IP、原因），用于异常登录追溯
"""
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Index
from sqlalchemy.sql import func

from backend.models.base import Base


class User(Base):
    """
    邮箱用户表

    安全要点：
    - email 唯一索引，作为唯一登录身份标识
    - password_hash 用 bcrypt 存储
    - email_verified 默认 False，未验证账号不可登录
    - verification_token 为一次性 URL token（明文存库，靠不可预测性保障；
      若需更高强度可改为存 sha256 摘要，这里平衡查询便利性）
    - failed_login_attempts / locked_until 实现连续 5 次失败锁定 15 分钟
    - last_login_ip 加密存储（utils.crypto），防止明文 IP 泄露
    """
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(254), unique=True, index=True, nullable=False)
    username = Column(String(64), nullable=False)
    avatar_url = Column(String(1024), nullable=True)
    avatar_object_key = Column(String(512), nullable=True)
    password_hash = Column(String(128), nullable=False)

    # 邮箱验证
    email_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    verification_token = Column(String(64), nullable=True, index=True)
    verification_expires_at = Column(DateTime(timezone=True), nullable=True)

    # 登录锁定策略
    failed_login_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # 上次登录信息（IP 加密存储）
    last_login_ip = Column(String(512), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} verified={self.email_verified}>"


class LoginLog(Base):
    """
    登录审计日志：每次登录尝试都记录，便于追溯异常登录 IP 与频次。
    """
    __tablename__ = "login_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=True, index=True)  # 未注册账号尝试登录时为 NULL
    email = Column(String(254), nullable=True, index=True)
    ip_address = Column(String(512), nullable=True)  # 加密存储
    success = Column(Boolean, nullable=False, default=False, server_default="false")
    failure_reason = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_login_logs_user_created", "user_id", "created_at"),
    )
