"""应用配置管理"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging

logger = logging.getLogger(__name__)


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

    # FastGPT配置
    FASTGPT_API_KEY: str = Field(
        default="",
        description="FastGPT API密钥"
    )
    FASTGPT_API_KEY_RD: str = Field(
        default="",
        description="FastGPT RD职位API密钥"
    )
    FASTGPT_API_KEY_MEDICAL: str = Field(
        default="",
        description="FastGPT Medical职位API密钥"
    )
    FASTGPT_BASE_URL: str = Field(
        default="http://localhost:3000",
        description="FastGPT API基础URL"
    )
    FASTGPT_CHAT_API: str = Field(
        default="/api/v1/chat/completions",
        description="FastGPT Chat Completions API路径"
    )
    FASTGPT_TIMEOUT: int = Field(
        default=120,
        description="FastGPT API超时时间（秒）"
    )

    # 阿里云OSS配置
    OSS_ACCESS_KEY_ID: str = Field(
        default="",
        description="阿里云OSS Access Key ID"
    )
    OSS_ACCESS_KEY_SECRET: str = Field(
        default="",
        description="阿里云OSS Access Key Secret"
    )
    OSS_BUCKET: str = Field(
        default="",
        description="阿里云OSS Bucket名称"
    )
    OSS_ENDPOINT: str = Field(
        default="",
        description="阿里云OSS Endpoint"
    )
    OSS_REGION: str = Field(
        default="",
        description="阿里云OSS Region"
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

    @field_validator('SECRET_KEY', 'ENCRYPTION_KEY')
    @classmethod
    def validate_security_keys(cls, v, info):
        """验证安全密钥在生产环境是否为默认值"""
        # 只在生产环境（DEBUG=False）进行严格检查
        # 获取DEBUG值，如果info.data中存在则使用，否则假设为False
        is_debug = info.data.get('DEBUG', False) if hasattr(info, 'data') else False

        if not is_debug:
            # 不安全的默认值列表
            insecure_defaults = [
                "your-secret-key-change-in-production",
                "your-encryption-key-32-bytes-long-change",
                ""
            ]
            if v in insecure_defaults:
                raise ValueError(
                    f"生产环境禁止使用不安全的默认密钥。"
                    f"请在环境变量中设置 {info.field_name}。"
                )
            # 检查密钥长度
            if len(v) < 32:
                raise ValueError(
                    f"{info.field_name} 长度必须至少32字符（当前：{len(v)}字符）"
                )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


def validate_settings(settings: Settings) -> None:
    """验证配置，生产环境拒绝不安全的默认值

    Args:
        settings: 配置对象

    Raises:
        ValueError: 配置验证失败
    """
    errors = []

    if not settings.DEBUG:
        # 生产环境检查
        if settings.SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("生产环境必须设置自定义 SECRET_KEY")
        if settings.ENCRYPTION_KEY == "your-encryption-key-32-bytes-long-change":
            errors.append("生产环境必须设置自定义 ENCRYPTION_KEY")
        if len(settings.SECRET_KEY) < 32:
            errors.append(f"SECRET_KEY 长度必须至少32字符（当前：{len(settings.SECRET_KEY)}）")
        if len(settings.ENCRYPTION_KEY) != 32:
            errors.append(f"ENCRYPTION_KEY 必须是32字节（当前：{len(settings.ENCRYPTION_KEY)}）")

    if errors:
        error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("配置验证通过")


settings = Settings()
