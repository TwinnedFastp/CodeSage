"""
认证接口：注册 / 邮箱验证 / 登录 / 登出 / 刷新令牌 / 当前用户
"""
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    VerifyEmailRequest,
)
from backend.services import auth_service

router = APIRouter()


def _client_ip(request: Request) -> str:
    """提取客户端真实 IP（优先取代理转发的 X-Forwarded-For 首段）。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """注册：仅邮箱 + 密码，注册后发送验证邮件。"""
    try:
        user, verify_link = await auth_service.register(payload.email, payload.password, db)
    except auth_service.AuthError as exc:
        return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})

    detail = f"注册成功，验证邮件已发送至 {user.email}（24 小时内有效）"
    # 开发模式下回传验证链接，方便联调；生产模式 verify_link 为 None
    if verify_link:
        detail += f"；开发模式验证链接：{verify_link}"
    return {"message": "注册成功", "detail": detail}


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """通过验证链接中的 token 完成邮箱验证。"""
    try:
        await auth_service.verify_email(payload.token, db)
    except auth_service.AuthError as exc:
        return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})
    return {"message": "邮箱验证成功，现在可以登录了"}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """邮箱 + 密码登录，返回 access + refresh 令牌。"""
    try:
        result = await auth_service.login(payload.email, payload.password, _client_ip(request), db)
    except auth_service.AuthError as exc:
        return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        expires_in=result["expires_in"],
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    """登出：吊销当前 access 令牌并清空该账号所有刷新令牌。"""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "", 1) if auth.lower().startswith("bearer ") else ""
    await auth_service.logout(token, db)
    return {"message": "已登出"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    """用 refresh_token 换取新的令牌对。"""
    try:
        result = await auth_service.refresh_tokens(payload.refresh_token)
    except auth_service.AuthError as exc:
        return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        expires_in=result["expires_in"],
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return current_user
