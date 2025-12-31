"""简历相关的Pydantic schemas"""
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class SkillsByLevel(BaseModel):
    """技能按熟练度分类"""
    expert: Optional[List[str]] = Field(default_factory=list, description="精通")
    proficient: Optional[List[str]] = Field(default_factory=list, description="熟悉")
    familiar: Optional[List[str]] = Field(default_factory=list, description="了解")
    mentioned: Optional[List[str]] = Field(default_factory=list, description="提及")


class ResumeBase(BaseModel):
    """简历基础信息"""
    candidate_name: Optional[str] = Field(None, description="候选人姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="电子邮箱")
    education: Optional[str] = Field(None, description="最高学历")
    work_years: Optional[int] = Field(None, description="工作年限")
    skills: Optional[List[str]] = Field(default_factory=list, description="技能标签")
    skills_by_level: Optional[SkillsByLevel] = Field(None, description="技能按熟练度分类")


class ResumeCreate(ResumeBase):
    """创建简历"""
    raw_text: Optional[str] = Field(None, description="简历原文")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_type: Optional[str] = Field(None, description="文件类型")
    work_experience: Optional[List[dict]] = Field(default_factory=list, description="工作经历")
    project_experience: Optional[List[dict]] = Field(default_factory=list, description="项目经历")
    education_history: Optional[List[dict]] = Field(default_factory=list, description="教育背景")


class ResumeUpdate(BaseModel):
    """更新简历"""
    candidate_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    education: Optional[str] = None
    work_years: Optional[int] = None
    skills: Optional[List[str]] = None
    status: Optional[str] = None


class ResumeResponse(ResumeBase):
    """简历响应"""
    id: UUID
    status: str
    work_experience: Optional[List[dict]] = []
    project_experience: Optional[List[dict]] = []
    education_history: Optional[List[dict]] = []
    raw_text: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    source_email_id: Optional[str] = None
    source_email_subject: Optional[str] = None
    source_sender: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    """简历列表响应"""
    total: int
    resumes: List[ResumeResponse]


class ResumeUploadResponse(BaseModel):
    """简历上传响应"""
    resume_id: UUID
    message: str
    auto_matched: bool = False
    top_matches: Optional[List[dict]] = Field(default_factory=list, description="最佳匹配结果（前2名）")
