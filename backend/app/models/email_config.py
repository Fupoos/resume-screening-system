"""邮箱配置模型"""
import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class EmailConfig(Base):
    """邮箱配置表"""
    __tablename__ = "email_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_address = Column(String(200), nullable=False, unique=True)
    auth_code_encrypted = Column(String(500), nullable=False)  # AES加密存储
    imap_server = Column(String(100), default="imap.exmail.qq.com")
    imap_port = Column(Integer, default=993)
    folder = Column(String(100), default="INBOX")
    processed_folder = Column(String(100), default="已处理")

    # 过滤配置
    filter_keywords = Column(JSONB, default=list)  # 过滤关键词列表
    sender_whitelist = Column(JSONB, default=list)  # 发件人白名单

    poll_interval = Column(Integer, default=300)  # 轮询间隔(秒)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
