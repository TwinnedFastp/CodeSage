"""
安全工具集：密码哈希、JWT 令牌、邮箱格式校验、密码复杂度校验

- 密码：bcrypt（passlib + bcrypt 后端），含复杂度策略
- 邮箱：基于 email-validator 的 RFC 合规校验 + 自定义业务规则
- JWT：access（7d 默认）+ refresh（30d 默认），jti 防重放，黑名单走 Redis
"""
from __future__ import annotations

import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from email_validator import EmailNotValidError, validate_email
from jose import JWTError, jwt

import bcrypt

from backend.core.config import settings

# ------------------------------------------------------------------
# 密码哈希（直接使用 bcrypt，避免 passlib 1.7.4 与 bcrypt>=4.1 的不兼容）
# ------------------------------------------------------------------
_BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """bcrypt 哈希密码，返回标准 $2b$ 开头的哈希字符串。"""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


# ------------------------------------------------------------------
# 密码复杂度策略
# ------------------------------------------------------------------
# 要求：>=8 位，包含大写、小写、数字、特殊字符各至少 1 个
_PWD_MIN_LEN = 8
_PWD_RULES = [
    (re.compile(r"[A-Z]"), "大写字母"),
    (re.compile(r"[a-z]"), "小写字母"),
    (re.compile(r"\d"), "数字"),
    (re.compile(r"[^A-Za-z0-9]"), "特殊字符"),
]


def validate_password_strength(password: str) -> Optional[str]:
    """
    校验密码复杂度。
    返回 None 表示通过；返回字符串为不满足的原因（中文）。
    """
    if not password or len(password) < _PWD_MIN_LEN:
        return f"密码长度不能少于 {_PWD_MIN_LEN} 位"
    missing = [name for pattern, name in _PWD_RULES if not pattern.search(password)]
    if missing:
        return f"密码必须至少包含：{'、'.join(missing)}"
    return None


# ------------------------------------------------------------------
# 邮箱格式校验（RFC 合规）
# ------------------------------------------------------------------
def validate_email_format(email: str) -> str:
    """
    校验邮箱格式是否符合 RFC 标准，并返回规范化（小写）邮箱。
    抛出 ValueError 表示不合法。
    """
    if not email or not isinstance(email, str):
        raise ValueError("邮箱不能为空")
    try:
        # validate_email 内部使用 idna + 正则做 RFC 校验
        validated = validate_email(email, check_deliverability=False)
    except EmailNotValidError as exc:
        # 兼容 email-validator 2.x：异常对象含 message
        raise ValueError(f"邮箱格式不合法：{exc}") from exc
    normalized = validated.normalized.lower()
    # 业务侧额外约束：长度上限 254（RFC 5321）
    if len(normalized) > 254:
        raise ValueError("邮箱长度超过 254 字符")
    return normalized


# ------------------------------------------------------------------
# JWT 令牌
# ------------------------------------------------------------------
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def _expire_delta(token_type: str) -> timedelta:
    if token_type == TOKEN_TYPE_REFRESH:
        return timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)


def create_token(user_id: int, token_type: str = TOKEN_TYPE_ACCESS) -> tuple[str, str, datetime]:
    """
    生成 JWT 令牌。
    返回 (token, jti, expires_at)。
    """
    now = datetime.now(timezone.utc)
    expires_at = now + _expire_delta(token_type)
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str) -> dict[str, Any]:
    """
    解码并校验 JWT（签名 + 过期时间）。
    抛出 JWTError 表示无效/过期。
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub", "type", "jti"]},
    )


# ------------------------------------------------------------------
# 验证令牌与一次性 token（邮箱验证链接）
# ------------------------------------------------------------------
def generate_token_urlsafe(nbytes: int = 32) -> str:
    """生成 URL 安全的随机 token（用于邮箱验证链接）。"""
    return secrets.token_urlsafe(nbytes)


def generate_verification_token() -> tuple[str, datetime]:
    """生成邮箱验证 token 与过期时间（默认 24 小时）。"""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFY_EXPIRE_HOURS)
    return generate_token_urlsafe(32), expires_at
