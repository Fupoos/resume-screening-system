"""用户模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserJobCategory(Base):
    """用户与岗位类别的关联表"""
    __tablename__ = "user_job_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_category_name = Column(String(100), nullable=False)  # 存储具体的岗位名称，如"Java开发"、"实施顾问"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 唯一约束：一个用户不能有重复的岗位类别分配
    __table_args__ = (
        UniqueConstraint('user_id', 'job_category_name', name='uq_user_job_category'),
    )

    # 关系
    user = relationship("User", back_populates="job_categories")


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # admin / user
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：用户可访问的岗位类别（多对多）
    job_categories = relationship(
        "UserJobCategory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
