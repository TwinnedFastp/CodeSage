"""
AI 模型供应商配置表

存储用户配置的多个 LLM/Embedding 供应商（如智谱、OpenAI、阿里百炼等），
支持动态切换、启用/禁用，替代硬编码的环境变量配置。

安全要点：
- llm_api_key 使用 Fernet 加密存储（utils/crypto）
- 按用户隔离，每个用户的供应商配置独立
- 同一用户可配置多个供应商，通过 is_enabled 控制活跃供应商
"""
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from backend.models.base import Base


class AIProvider(Base):
    """
    AI 模型供应商配置表

    每条记录代表一个供应商配置（如智谱 GLM、OpenAI GPT 等），
    用户可以添加多个供应商并启用/禁用。
    """
    __tablename__ = "ai_providers"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 供应商基本信息
    provider_name = Column(String(64), nullable=False)  # 如 "智谱 GLM", "OpenAI", "阿里百炼"

    # LLM 配置
    llm_api_key = Column(String(512), nullable=False)  # 加密存储
    llm_base_url = Column(String(512), nullable=False)  # API endpoint
    llm_model = Column(String(128), nullable=False)  # 如 glm-4.5-air, gpt-4o

    # Embedding 配置
    embedding_model = Column(String(128), nullable=False)  # 如 embedding-3, text-embedding-3-small
    embedding_dim = Column(Integer, nullable=False, default=1024)

    # 状态控制
    is_enabled = Column(Boolean, nullable=False, default=True, server_default="true")

    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_ai_providers_user_enabled", "user_id", "is_enabled"),
    )

    def __repr__(self) -> str:
        return (
            f"<AIProvider id={self.id} name={self.provider_name} "
            f"model={self.llm_model} enabled={self.is_enabled}>"
        )
