"""
认证服务：注册 / 登录 / 登出 / 邮箱验证 / 令牌刷新

安全要点：
- 注册：RFC 邮箱校验 + 唯一性 + 密码复杂度 + bcrypt + 发验证邮件（24h）
- 登录：邮箱必须已验证；5 次失败锁 15 分钟；记录 IP；JWT access(7d)+refresh(30d)
- 登出：access 进 Redis 黑名单 + 删除 refresh 白名单记录
- 刷新：校验 refresh 有效性 + 类型 + Redis 白名单后签发新令牌对
所有 DB 操作均在事务中执行，异常自动回滚。
"""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

# boto3 / botocore 已迁移到 backend.minio 模块，这里不再直接导入
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core import redis_client
from backend.core.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_token,
    decode_token,
    generate_verification_token,
    hash_password,
    validate_email_format,
    validate_password_strength,
    verify_password,
)
from backend.models.user import User, LoginLog
from backend.services import email_service
from backend.utils.crypto import encrypt

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 自定义异常
# ------------------------------------------------------------------
class AuthError(Exception):
    """认证业务异常基类。"""

    def __init__(self, message: str, code: str = "auth_error", status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


# ------------------------------------------------------------------
# 注册
# ------------------------------------------------------------------
def normalize_username(username: Optional[str], email: str) -> str:
    value = (username or email.split("@", 1)[0]).strip()
    value = re.sub(r"[\x00-\x1f\x7f]+", "", value)
    value = re.sub(r"\s+", " ", value)
    if len(value) < 2:
        value = email.split("@", 1)[0]
    return value[:64]


async def register(email: str, password: str, db: AsyncSession, username: Optional[str] = None) -> tuple[User, Optional[str]]:
    """
    注册新用户。
    返回 (user, verify_link_or_none)。verify_link 仅开发模式回传。
    """
    # 1. RFC 邮箱校验
    try:
        email = validate_email_format(email)
    except ValueError as exc:
        raise AuthError(str(exc), code="invalid_email", status=422)

    # 2. 密码复杂度
    err = validate_password_strength(password)
    if err:
        raise AuthError(err, code="weak_password", status=422)

    # 3. 唯一性校验
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise AuthError("该邮箱已被注册", code="email_exists", status=409)

    # 4. 创建用户
    verify_token, expires_at = generate_verification_token()
    user = User(
        email=email,
        username=normalize_username(username, email),
        password_hash=hash_password(password),
        email_verified=False,
        verification_token=verify_token,
        verification_expires_at=expires_at,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AuthError("该邮箱已被注册", code="email_exists", status=409)
    except Exception:
        await db.rollback()
        logger.exception("注册写库失败")
        raise AuthError("注册失败，请稍后重试", code="db_error", status=500)
    await db.refresh(user)
    if not user.avatar_url:
        user.avatar_url = _default_avatar_url(user.id)
        await db.commit()
        await db.refresh(user)

    # 5. 发送验证邮件
    try:
        link = await email_service.send_verification_email(user.email, verify_token)
    except RuntimeError:
        logger.warning("注册成功但验证邮件发送失败 user_id=%s", user.id)
        link = None

    return user, link


# ------------------------------------------------------------------
# 邮箱验证
# ------------------------------------------------------------------
async def verify_email(token: str, db: AsyncSession) -> User:
    """校验邮箱验证 token，标记账号为已验证。"""
    if not token:
        raise AuthError("验证 token 不能为空", code="invalid_token", status=422)

    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("验证 token 无效", code="invalid_token", status=404)

    if user.email_verified:
        return user

    if user.verification_expires_at is None or user.verification_expires_at < datetime.now(timezone.utc):
        raise AuthError("验证链接已过期，请重新申请", code="token_expired", status=410)

    try:
        await db.execute(
            update(User)
            .where(User.id == user.id)
            .values(email_verified=True, verification_token=None, verification_expires_at=None)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("邮箱验证写库失败 user_id=%s", user.id)
        raise AuthError("验证失败，请稍后重试", code="db_error", status=500)

    user.email_verified = True
    return user


# ------------------------------------------------------------------
# 登录
# ------------------------------------------------------------------
async def login(email: str, password: str, client_ip: Optional[str], db: AsyncSession) -> dict:
    """
    邮箱 + 密码登录。
    返回 {access_token, refresh_token, expires_in, user}。
    """
    try:
        email = validate_email_format(email)
    except ValueError as exc:
        raise AuthError(str(exc), code="invalid_email", status=422)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    async def _log_login(success: bool, reason: Optional[str]) -> None:
        try:
            db.add(LoginLog(
                user_id=user.id if user else None,
                email=email,
                ip_address=encrypt(client_ip) if client_ip else None,
                success=success,
                failure_reason=reason,
            ))
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("写登录日志失败")

    # 账号不存在：明确提示用户需要注册
    if user is None:
        await _log_login(False, "user_not_found")
        raise AuthError("该邮箱尚未注册，请先注册", code="user_not_found", status=401)

    # 账号锁定检查
    if user.locked_until and user.locked_until > now:
        remain = int((user.locked_until - now).total_seconds() // 60) + 1
        await _log_login(False, f"account_locked({remain}min)")
        raise AuthError(
            f"账号已锁定，请约 {remain} 分钟后重试",
            code="account_locked",
            status=423,
        )

    # 密码校验
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        attempts = user.failed_login_attempts

        if attempts >= settings.LOGIN_MAX_FAIL_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
            user.failed_login_attempts = 0  # 锁定后清零，解锁重新计数
            try:
                await db.commit()
            except Exception:
                await db.rollback()
            await _log_login(False, f"locked_after_{attempts}_fails")
            raise AuthError(
                f"连续 {settings.LOGIN_MAX_FAIL_ATTEMPTS} 次密码错误，账号已锁定 {settings.LOGIN_LOCK_MINUTES} 分钟",
                code="account_locked",
                status=423,
            )
        else:
            try:
                await db.commit()
            except Exception:
                await db.rollback()
            await _log_login(False, f"wrong_password({attempts}/{settings.LOGIN_MAX_FAIL_ATTEMPTS})")
            raise AuthError(
                f"邮箱或密码错误（剩余尝试 {settings.LOGIN_MAX_FAIL_ATTEMPTS - attempts} 次）",
                code="invalid_credentials",
                status=401,
            )

    # 密码正确，但邮箱未验证（开发模式可通过 SKIP_EMAIL_VERIFICATION 绕过）
    if not user.email_verified and not settings.SKIP_EMAIL_VERIFICATION:
        await _log_login(False, "email_not_verified")
        raise AuthError("邮箱尚未验证，请先完成验证", code="email_not_verified", status=403)

    # 登录成功：重置失败计数、记录登录信息
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    user.last_login_ip = encrypt(client_ip) if client_ip else None
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("更新登录信息失败 user_id=%s", user.id)
        raise AuthError("登录失败，请稍后重试", code="db_error", status=500)
    await _log_login(True, None)

    # 签发令牌
    access_token, access_jti, _ = create_token(user.id, TOKEN_TYPE_ACCESS)
    refresh_token, refresh_jti, _ = create_token(user.id, TOKEN_TYPE_REFRESH)

    # refresh 白名单写入 Redis
    await redis_client.store_refresh_token(
        user.id, refresh_jti, settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400,
        "user": user,
    }


def _sanitize_avatar_filename(filename: str) -> str:
    """头像文件名清理（委托给 minio 模块）。"""
    from backend.minio import sanitize_filename
    return sanitize_filename(filename) or "avatar"


def _default_avatar_url(user_id: int) -> str:
    seed = f"{user_id}-{settings.PROJECT_NAME}"
    return f"https://api.dicebear.com/7.x/initials/svg?seed={seed}"


# ------------------------------------------------------------------
# 用户资料
# ------------------------------------------------------------------
async def update_profile(user: User, username: str, db: AsyncSession) -> User:
    normalized = normalize_username(username, user.email)
    if not normalized:
        raise AuthError("用户名不能为空", code="invalid_username", status=422)

    user.username = normalized
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("更新用户资料失败 user_id=%s", user.id)
        raise AuthError("保存失败，请稍后重试", code="db_error", status=500)
    await db.refresh(user)
    return user


async def issue_avatar_upload(user: User, filename: str, content_type: str) -> dict:
    """
    生成头像预签名上传 URL（委托给 minio 模块）。

    object_key 格式：avatars/{user_id}/{uuid}-{filename}
    """
    from backend.minio import generate_presigned_upload_url, is_s3_enabled

    if not is_s3_enabled():
        raise AuthError("头像存储未启用，请检查 MinIO/S3 配置", code="s3_disabled", status=503)

    object_key = f"avatars/{user.id}/{uuid.uuid4().hex}-{_sanitize_avatar_filename(filename)}"
    try:
        result = await generate_presigned_upload_url(
            object_key=object_key,
            content_type=content_type,
            bucket=settings.S3_BUCKET_AVATARS,
        )
        return result
    except RuntimeError as exc:
        raise AuthError(str(exc), code="s3_error", status=502) from exc


async def commit_avatar(user: User, object_key: str, avatar_url: str, db: AsyncSession) -> User:
    if not object_key.startswith(f"avatars/{user.id}/"):
        raise AuthError("头像对象不属于当前用户", code="invalid_avatar", status=403)
    user.avatar_object_key = object_key
    user.avatar_url = avatar_url
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("更新头像失败 user_id=%s", user.id)
        raise AuthError("头像保存失败，请稍后重试", code="db_error", status=500)
    await db.refresh(user)
    return user


# ------------------------------------------------------------------
# 登出
# ------------------------------------------------------------------
async def logout(access_token: str, db: AsyncSession) -> None:
    """登出：access 进黑名单 + refresh 白名单删除。"""
    try:
        payload = decode_token(access_token)
    except Exception:
        # 无效令牌登出视为无操作
        return

    if payload.get("type") != TOKEN_TYPE_ACCESS:
        return

    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now)
        if ttl > 0:
            await redis_client.blacklist_token(jti, ttl)

    user_id = int(payload["sub"])
    # 吊销该用户全部刷新令牌（登出即踢出该账号所有会话刷新能力）
    await redis_client.revoke_all_refresh_tokens(user_id)


# ------------------------------------------------------------------
# 令牌刷新
# ------------------------------------------------------------------
async def refresh_tokens(refresh_token: str) -> dict:
    """用 refresh_token 换取新的令牌对。"""
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise AuthError("刷新令牌无效或已过期", code="invalid_refresh", status=401)

    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise AuthError("令牌类型错误", code="invalid_refresh", status=401)

    user_id = int(payload["sub"])
    jti = payload.get("jti")
    if not jti or not await redis_client.is_refresh_token_valid(user_id, jti):
        raise AuthError("刷新令牌已被吊销", code="invalid_refresh", status=401)

    # 旋转令牌：吊销旧 refresh，签发新对
    await redis_client.revoke_refresh_token(user_id, jti)
    new_access, _, _ = create_token(user_id, TOKEN_TYPE_ACCESS)
    new_refresh, new_refresh_jti, _ = create_token(user_id, TOKEN_TYPE_REFRESH)
    await redis_client.store_refresh_token(
        user_id, new_refresh_jti, settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    }


# ------------------------------------------------------------------
# 当前用户解析（依赖注入用）
# ------------------------------------------------------------------
async def resolve_current_user(access_token: str, db: AsyncSession) -> User:
    """解析 access token 并返回用户对象；校验黑名单。"""
    try:
        payload = decode_token(access_token)
    except Exception:
        raise AuthError("令牌无效或已过期", code="invalid_token", status=401)

    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise AuthError("令牌类型错误", code="invalid_token", status=401)

    jti = payload.get("jti")
    if jti and await redis_client.is_token_blacklisted(jti):
        raise AuthError("令牌已失效，请重新登录", code="token_revoked", status=401)

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("用户不存在", code="user_not_found", status=401)
    return user
