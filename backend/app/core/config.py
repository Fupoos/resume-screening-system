"""应用配置管理"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "简历智能初筛系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://resume:resume123@db:5432/resume_screening",
        description="数据库连接URL"
    )

    # Redis配置
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        description="Redis连接URL"
    )

    # JWT配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 加密配置
    ENCRYPTION_KEY: str = Field(
        default="your-encryption-key-32-bytes-long-change",
        description="AES加密密钥，必须是32字节"
    )

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    # Celery配置
    CELERY_BROKER_URL: str = Field(
        default="redis://redis:6379/0",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://redis:6379/0",
        description="Celery result backend"
    )

    # 邮箱配置（默认值）
    DEFAULT_IMAP_SERVER: str = "imap.exmail.qq.com"
    DEFAULT_IMAP_PORT: int = 993

    # Agent配置
    AGENT_API_KEY: str = Field(
        default="",
        description="外部Agent API密钥"
    )
    AGENT_TIMEOUT: int = Field(
        default=30,
        description="Agent调用超时时间（秒）"
    )
    AGENT_RETRY_COUNT: int = Field(
        default=3,
        description="Agent调用重试次数"
    )
    PDF_BASE_URL: str = Field(
        default="http://localhost:8000",
        description="PDF文件访问基础URL"
    )

    # 邮箱监听配置
    DEMO_EMAIL: str = Field(
        default="",
        description="演示邮箱地址"
    )
    DEMO_AUTH_CODE: str = Field(
        default="",
        description="邮箱授权码"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
