from fastapi import APIRouter
from backend.api.v1.endpoints import auth, chat, conversations, providers
from backend.rag import endpoints as rag

api_router = APIRouter()

# 认证模块：注册 / 登录 / 登出 / 邮箱验证 / 令牌刷新 / 当前用户
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# 聊天模块
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# LLM 会话存储模块：会话 / 消息 / 偏好 / 事实记忆 / 任务
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
# AI 供应商配置管理
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
# PostgreSQL 数据库管理（仅表数据 CRUD，不开放任意 SQL）
api_router.include_router(database_admin.router, prefix="/database-admin", tags=["database-admin"])
# LightRAG 知识库模块（统一在 backend.rag 包中管理）
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
