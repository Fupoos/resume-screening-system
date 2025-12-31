"""数据库连接配置"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# 创建同步引擎
engine = create_engine(
    settings.DATABASE_URL.replace('+asyncpg', ''),  # 使用同步驱动 psycopg2
    echo=settings.DEBUG,
    future=True
)

# 创建同步会话工厂
SessionLocal = sessionmaker(
    engine,
    autocommit=False,
    autoflush=False
)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
