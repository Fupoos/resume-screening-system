"""筛选相关的Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID


class ScreeningRequest(BaseModel):
    """筛选请求"""
    resume_id: UUID = Field(..., description="简历ID")
    job_id: UUID = Field(..., description="岗位ID")


class ScreeningResponse(BaseModel):
    """筛选结果"""
    id: UUID
    resume_id: UUID
    job_id: UUID
    match_score: int
    skill_score: int
    experience_score: int
    education_score: int
    screening_result: str  # PASS / REVIEW / REJECT
    matched_points: List[str]
    unmatched_points: List[str]
    suggestion: Optional[str] = None

    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    """匹配请求（不保存到数据库）"""
    candidate_name: str = Field(..., description="候选人姓名")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    education: Optional[str] = Field(None, description="学历")
    work_years: Optional[int] = Field(None, description="工作年限")
    skills: List[str] = Field(default_factory=list, description="技能列表")
    job_id: UUID = Field(..., description="岗位ID")
