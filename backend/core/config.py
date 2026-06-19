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
    # 留空时由 crypto 模块生成临时密钥（仅限开发，重启后无法解密历史数据）
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

    # LightRAG 配置
    # LIGHTRAG_WORKING_DIR 用来存放 LightRAG 生成的索引、图谱和缓存文件。
    # 放在 backend/data/lightrag 下，方便开发时直接查看这些学习材料。
    LIGHTRAG_WORKING_DIR: str = "data/lightrag"
    # 是否启用 LightRAG。关闭后，RAG 接口会给出明确提示，普通聊天仍可使用。
    LIGHTRAG_ENABLED: bool = True
    # 默认使用阿里云百炼 OpenAI 兼容接口。
    # 以后要切换 DeepSeek、硅基流动、OpenRouter 等平台，只需要改下面几个 LLM_* 配置。
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"
    EMBEDDING_MODEL: str = "text-embedding-v4"
    EMBEDDING_DIM: int = 1024
    # 兼容常见环境变量名：阿里百炼官方常用 DASHSCOPE_API_KEY，OpenAI 常用 OPENAI_API_KEY。
    DASHSCOPE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""

    @property
    def lightrag_api_key(self) -> str:
        """
        获取 LightRAG 使用的大模型 API Key。

        优先级：
        1. LLM_API_KEY：项目统一配置，推荐使用
        2. DASHSCOPE_API_KEY：阿里百炼官方环境变量名
        3. OPENAI_API_KEY：兼容 OpenAI 或其它旧配置
        """
        return self.LLM_API_KEY or self.DASHSCOPE_API_KEY or self.OPENAI_API_KEY

    @property
    def lightrag_base_url(self) -> str:
        """
        获取 OpenAI 兼容接口地址。

        LLM_BASE_URL 默认指向阿里百炼大陆地域；如果你已有 OPENAI_BASE_URL，也可以继续复用。
        """
        return self.LLM_BASE_URL or self.OPENAI_BASE_URL

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
