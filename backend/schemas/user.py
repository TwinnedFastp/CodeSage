from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """
    用户基础 Schema，包含公共字段
    """
    email: EmailStr
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    """
    创建用户时的 Schema，包含密码
    """
    password: str

class UserUpdate(UserBase):
    """
    更新用户时的 Schema，所有字段可选
    """
    password: Optional[str] = None

class UserInDBBase(UserBase):
    """
    数据库中用户的 Schema 基础类
    """
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    """
    返回给客户端的用户 Schema
    """
    pass
