from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.api import api_router
from backend.core.config import settings

# --- 初始化 FastAPI 应用 ---
# title: 自动生成的 API 文档标题
# openapi_url: OpenAPI 规范文件的路径
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

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
