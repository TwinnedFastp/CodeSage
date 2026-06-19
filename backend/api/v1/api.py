from fastapi import APIRouter
from backend.api.v1.endpoints import chat

api_router = APIRouter()

# 包含聊天模块的路由，并设置前缀和标签
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
