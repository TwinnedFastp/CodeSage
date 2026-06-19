"""
认证相关 FastAPI 依赖：
- 从 Authorization 头解析 Bearer token
- 校验黑名单并加载当前用户
"""
from __future__ import annotations

from fastapi import Depends, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.user import User
from backend.services.auth_service import AuthError, resolve_current_user

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """解析并返回当前登录用户。未携带/无效令牌抛 401。"""
    if credentials is None or not credentials.credentials:
        raise AuthError("未提供认证令牌", code="no_token", status=status.HTTP_401_UNAUTHORIZED)
    return await resolve_current_user(credentials.credentials, db)
