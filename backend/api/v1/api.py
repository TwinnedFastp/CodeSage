from fastapi import APIRouter
from backend.api.v1.endpoints import auth, chat, conversations, rag

api_router = APIRouter()

# 认证模块：注册 / 登录 / 登出 / 邮箱验证 / 令牌刷新 / 当前用户
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# 聊天模块
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# LLM 会话存储模块：会话 / 消息 / 偏好 / 事实记忆 / 任务
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
# LightRAG 知识库模块
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
