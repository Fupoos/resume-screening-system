"""岗位相关的Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class JobBase(BaseModel):
    """岗位基础模型"""
    name: str = Field(..., description="岗位名称")
    category: str = Field(..., description="岗位类别: hr/software/finance/sales")
    description: Optional[str] = Field(None, description="岗位描述")
    required_skills: List[str] = Field(default_factory=list, description="必备技能")
    preferred_skills: List[str] = Field(default_factory=list, description="加分技能")
    min_work_years: int = Field(0, description="最低工作年限")
    min_education: str = Field("大专", description="最低学历")
    skill_weight: int = Field(50, description="技能权重")
    experience_weight: int = Field(30, description="经验权重")
    education_weight: int = Field(20, description="学历权重")
    pass_threshold: int = Field(70, description="PASS阈值")
    review_threshold: int = Field(50, description="REVIEW阈值")


class JobCreate(JobBase):
    """创建岗位"""
    pass


class JobUpdate(BaseModel):
    """更新岗位"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_work_years: Optional[int] = None
    min_education: Optional[str] = None
    skill_weight: Optional[int] = None
    experience_weight: Optional[int] = None
    education_weight: Optional[int] = None
    pass_threshold: Optional[int] = None
    review_threshold: Optional[int] = None
    is_active: Optional[bool] = None


class JobResponse(JobBase):
    """岗位响应"""
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True
