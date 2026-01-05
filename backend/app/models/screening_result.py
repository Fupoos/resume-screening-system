"""筛选结果模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class ScreeningResult(Base):
    """筛选结果表"""
    __tablename__ = "screening_results"
    __table_args__ = (
        UniqueConstraint('resume_id', 'job_id', name='uq_resume_job'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=False)

    # Agent评估分数
    agent_score = Column(Integer)  # Agent评分 0-100

    # 匹配详情
    matched_points = Column(JSONB, default=list)  # 关键匹配点
    unmatched_points = Column(JSONB, default=list)  # 不匹配点
    match_details = Column(JSONB, default=dict)  # 匹配详情

    # 筛选结果
    screening_result = Column(String(20))  # PASS / REVIEW / REJECT
    confidence = Column(Numeric(3, 2))  # 置信度
    suggestion = Column(Text)  # 建议说明

    # 处理信息
    processing_time_ms = Column(Integer)  # 处理耗时(毫秒)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
