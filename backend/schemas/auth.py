"""
认证相关 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """注册请求：仅邮箱 + 密码"""
    email: str = Field(..., description="邮箱（RFC 合规）")
    password: str = Field(..., description="密码（>=8位，含大小写/数字/特殊字符）")


class LoginRequest(BaseModel):
    """登录请求：仅邮箱 + 密码"""
    email: str
    password: str


class TokenResponse(BaseModel):
    """登录/刷新成功返回的令牌"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="access token 有效期（秒）")


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class UserOut(BaseModel):
    """对外返回的用户信息（不含密码）"""
    id: int
    email: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
