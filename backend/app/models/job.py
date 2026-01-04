"""岗位模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class Job(Base):
    """岗位模型表"""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # hr/software/finance/sales
    description = Column(Text)

    # 技能要求
    required_skills = Column(JSONB, default=list)  # 必备技能
    preferred_skills = Column(JSONB, default=list)  # 加分技能

    # 其他要求
    min_work_years = Column(Integer, default=0)  # 最低工作年限
    min_education = Column(String(50), default="大专")  # 最低学历

    # 规则权重配置
    skill_weight = Column(Integer, default=50)  # 技能权重
    experience_weight = Column(Integer, default=30)  # 经验权重
    education_weight = Column(Integer, default=20)  # 学历权重

    # 筛选阈值
    pass_threshold = Column(Integer, default=70)  # PASS阈值
    review_threshold = Column(Integer, default=50)  # REVIEW阈值

    # Agent配置
    agent_type = Column(String(20), default="http")  # Agent类型：http/fastgpt
    agent_url = Column(String(500))  # Agent endpoint URL
    agent_timeout = Column(Integer, default=30)  # 超时时间（秒）
    agent_retry = Column(Integer, default=3)  # 重试次数

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
