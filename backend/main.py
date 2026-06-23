from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.v1.api import api_router
from backend.core.config import settings
from backend.init_db import init_db
from backend.services.auth_service import AuthError
from backend.services.conversation_service import ConversationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


# --- 初始化 FastAPI 应用 ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# --- 全局异常处理器 ---
# 把业务层抛出的自定义异常统一转换为 JSON 响应，避免 500 泄露堆栈
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})


@app.exception_handler(ConversationError)
async def conversation_error_handler(request: Request, exc: ConversationError):
    return JSONResponse(status_code=exc.status, content={"message": exc.message})

# --- 配置跨域资源共享 (CORS) ---
# 这非常重要，否则前端 (localhost:5173) 无法请求后端 (localhost:8000)
# BACKEND_CORS_ORIGINS 在 core/config.py 中配置
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE 等)
        allow_headers=["*"],  # 允许所有请求头
    )

# --- 注册 API 路由 ---
# 将所有定义在 api_router 中的接口挂载到 /api/v1 前缀下
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """
    根路由接口
    返回一个简单的欢迎信息，用于测试后端是否正常启动。
    """
    return {"message": f"欢迎使用 {settings.PROJECT_NAME} API"}

@app.get("/health")
async def health_check():
    """
    健康检查接口
    Docker 或负载均衡器可以使用此接口来判断服务是否存活。
    """
    return {"status": "healthy"}
