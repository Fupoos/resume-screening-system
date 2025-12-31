"""简历模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class Resume(Base):
    """简历表"""
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))

    # 基本信息
    education = Column(String(50))  # 最高学历
    education_level = Column(String(20))  # 学历等级标注：985/211/双非/QS前50/QS前100
    work_years = Column(Integer)  # 工作年限

    # 结构化��据（JSONB）
    skills = Column(JSONB, default=list)  # 技能标签数组
    skills_by_level = Column(JSONB, default=None)  # 技能按熟练度分类 {expert: [], proficient: [], familiar: [], mentioned: []}
    work_experience = Column(JSONB, default=list)  # 工作经历数组
    project_experience = Column(JSONB, default=list)  # 项目经历数组
    education_history = Column(JSONB, default=list)  # 教育背景数组

    # 原始数据
    raw_text = Column(Text)  # 简历原文
    file_path = Column(String(500))  # 原始文件路径
    file_type = Column(String(20))  # pdf/docx

    # 来源信息
    source_email_id = Column(String(200))  # 来源邮件ID
    source_email_subject = Column(String(500))  # 邮件主题
    source_sender = Column(String(200))  # 发件人

    # 地理和分类信息
    city = Column(String(50))  # 提取的城市（如"北京"、"上海"、"未知"）
    job_category = Column(String(20))  # hr/software/finance/sales/uncategorized

    # PDF相关
    pdf_path = Column(String(500))  # 合并后的PDF路径（邮件正文+附件）

    # Agent评估结果
    agent_score = Column(Integer)  # 外部agent评分(0-100)
    agent_evaluation_id = Column(String(100))  # agent评估ID
    agent_evaluated_at = Column(DateTime)  # agent评估时间

    # 筛选结果
    screening_status = Column(String(20), default="pending")  # 不合格/待定/���以发offer

    # 处理状态
    status = Column(String(20), default="pending")  # pending/parsed/processed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
