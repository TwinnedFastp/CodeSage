"""
AI 供应商配置的请求/响应 Schema
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    """创建供应商配置"""
    provider_name: str = Field(..., min_length=1, max_length=64)
    llm_api_key: str = Field(..., min_length=1, max_length=512)
    llm_base_url: str = Field(..., min_length=1, max_length=512)
    llm_model: str = Field(..., min_length=1, max_length=128)
    embedding_model: str = Field(..., min_length=1, max_length=128)
    embedding_dim: int = Field(..., ge=1, le=8192)


class ProviderUpdate(BaseModel):
    """更新供应商配置（全部可选）"""
    provider_name: str | None = Field(None, max_length=64)
    llm_api_key: str | None = Field(None, max_length=512)
    llm_base_url: str | None = Field(None, max_length=512)
    llm_model: str | None = Field(None, max_length=128)
    embedding_model: str | None = Field(None, max_length=128)
    embedding_dim: int | None = Field(None, ge=1, le=8192)
    is_enabled: bool | None = None


class ProviderOut(BaseModel):
    """供应商配置响应（API Key 脱敏）"""
    id: int
    provider_name: str
    llm_api_key: str  # 脱敏后的 key（如 sk-***abc123）
    llm_base_url: str
    llm_model: str
    embedding_model: str
    embedding_dim: int
    is_enabled: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
