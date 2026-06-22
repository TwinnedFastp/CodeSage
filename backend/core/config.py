from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    全局配置类
    使用 Pydantic 自动从环境变量或 .env 文件中读取配置。
    """
    # API 基础路径
    API_V1_STR: str = "/api/v1"
    # 项目名称
    PROJECT_NAME: str = "ChatGPT Clone"
    
    # CORS 跨域配置：允许访问后端的域名列表
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # 数据库配置信息
    # 默认连接到名为 'db' 的服务，这是 docker-compose.yml 中定义的数据库容器名
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "chatgpt_clone"
    # 如果手动指定了 DATABASE_URL，则优先使用
    DATABASE_URL: str = ""

    # ---- Redis 配置 ----
    # 容器内：redis://redis:6379/0 ；本地直连：redis://localhost:6379/0
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- JWT 配置 ----
    # 生产环境必须通过环境变量注入高熵随机字符串
    JWT_SECRET: str = "please-change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    # 登录令牌（access）有效期，单位：天
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    # 刷新令牌有效期，单位：天
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ---- 字段级加密密钥（Fernet，base64 urlsafe）----
    # 留空时由 crypto 模块基于 JWT_SECRET 派生稳定密钥（开发兜底，跨重启可复用）。
    # 生产环境务必显式配置一个高熵随机字符串，且变更后历史加密数据将无法解密。
    FIELD_ENCRYPTION_KEY: str = ""

    # ---- 邮箱验证 / SMTP 配置 ----
    # 验证链接前缀，前端可访问地址
    VERIFY_EMAIL_BASE_URL: str = "http://localhost:80"
    # SMTP 留空时验证邮件内容打印到日志（开发模式）
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # ---- 登录安全策略 ----
    LOGIN_MAX_FAIL_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 15
    EMAIL_VERIFY_EXPIRE_HOURS: int = 24
    # 开发模式：设为 true 时跳过邮箱验证检查，方便本地联调（生产环境务必 false）
    SKIP_EMAIL_VERIFICATION: bool = False

    # ---- LightRAG 系统级配置 ----
    # LIGHTRAG_WORKING_DIR 用来存放 LightRAG 生成的索引、图谱和缓存文件。
    # 放在 backend/data/lightrag 下，方便开发时直接查看这些学习材料。
    LIGHTRAG_WORKING_DIR: str = "data/lightrag"
    # 是否启用 LightRAG。关闭后，RAG 接口会给出明确提示，普通聊天仍可使用。
    LIGHTRAG_ENABLED: bool = True
    # 是否使用离线分词器（默认开启，适合国内无法访问 tiktoken 词表 CDN 的环境）。
    # 开启时注入纯 Python 分词器，跳过 tiktoken 远程下载 o200k_base；
    # 关闭后回退到 LightRAG 默认的 TiktokenTokenizer（需能访问 Azure Blob）。
    RAG_OFFLINE_TOKENIZER: bool = True
    # 注意：AI 模型供应商配置（API Key / Base URL / 模型名 / Embedding 维度等）
    # 已迁移至数据库 ai_providers 表，通过前端「设置 → 模型供应商」页面管理。
    # 每个用户可配置多个供应商并启用其中一个，无需在 .env 中配置 LLM 相关项。

    class Config:
        # 环境变量名称区分大小写
        case_sensitive = True
        # 指定环境变量文件的位置
        env_file = ".env"

    @property
    def async_database_url(self) -> str:
        """
        生成 SQLAlchemy 异步连接字符串
        格式: postgresql+asyncpg://user:password@host/dbname
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

# 实例化配置对象，供整个项目使用
settings = Settings()
