"""Agent解析历史模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class AgentParsingHistory(Base):
    """Agent解析历史记录表"""
    __tablename__ = "agent_parsing_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 关联简历
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)

    # Agent信息
    agent_type = Column(String(50), default="fastgpt")  # fastgpt/other
    agent_version = Column(String(50))  # Agent版本号

    # 请求/响应
    request_payload = Column(JSONB, default=None)  # 发送给Agent的完整请求
    response_data = Column(JSONB, default=None)  # Agent返回的完整响应

    # 解析结果
    parsed_candidate_name = Column(String(100))  # 解析出的候选人姓名
    parsed_job_title = Column(String(100))  # 解析出的职位
    job_confidence = Column(Integer)  # 职位分类置信度 (0-100)

    parsing_success = Column(Boolean, default=True)  # 解析是否成功
    error_message = Column(Text)  # 错误信息

    # 性能
    processing_time_ms = Column(Integer)  # 处理耗时（毫秒）

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
