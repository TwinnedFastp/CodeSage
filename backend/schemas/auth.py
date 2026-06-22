"""
认证相关 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """注册请求：邮箱 + 密码 + 用户名"""
    email: str = Field(..., description="邮箱（RFC 合规）")
    password: str = Field(..., description="密码（>=8位，含大小写/数字/特殊字符）")
    username: Optional[str] = Field(None, min_length=2, max_length=64, description="用户名")


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
    username: str
    avatar_url: Optional[str] = None
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64, description="用户名")


class AvatarUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., pattern="^image/(png|jpeg|jpg|webp|gif)$")


class AvatarUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    public_url: str
    expires_in: int


class AvatarCommitRequest(BaseModel):
    object_key: str = Field(..., min_length=1, max_length=512)
    avatar_url: str = Field(..., min_length=1, max_length=1024)
