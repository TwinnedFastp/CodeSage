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
