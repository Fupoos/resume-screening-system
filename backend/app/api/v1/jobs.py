"""岗位相关API路由

根据CLAUDE.md核心原则：
- 不使用本地JobMatcher进行匹配
- 岗位信息仅用于展示和传递给外部Agent
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app.schemas.job import JobCreate, JobUpdate, JobResponse

router = APIRouter()

# 临时内存存储（后续改为数据库）
jobs_db = {}

# 预设4种岗位
preset_jobs = [
    {
        'id': UUID('00000000-0000-0000-0000-000000000001'),
        'name': 'HR专员',
        'category': 'hr',
        'description': '负责招聘、培训、绩效管理等人力资源工作',
        'required_skills': ['招聘', '培训', '绩效管理'],
        'preferred_skills': ['HRIS系统', '薪酬管理'],
        'min_work_years': 1,
        'min_education': '大专',
        'skill_weight': 50,
        'experience_weight': 30,
        'education_weight': 20,
        'pass_threshold': 70,
        'review_threshold': 50,
        'is_active': True
    },
    {
        'id': UUID('00000000-0000-0000-0000-000000000002'),
        'name': 'Python后端工程师',
        'category': 'software',
        'description': '负责后端系统开发',
        'required_skills': ['Python', 'FastAPI'],
        'preferred_skills': ['MySQL', 'Redis', 'Docker'],
        'min_work_years': 2,
        'min_education': '本科',
        'skill_weight': 50,
        'experience_weight': 30,
        'education_weight': 20,
        'pass_threshold': 70,
        'review_threshold': 50,
        'is_active': True
    },
    {
        'id': UUID('00000000-0000-0000-0000-000000000003'),
        'name': '财务专员',
        'category': 'finance',
        'description': '负责财务核算、报表编制等工作',
        'required_skills': ['财务报表', '会计', 'Excel'],
        'preferred_skills': ['税务', '审计'],
        'min_work_years': 2,
        'min_education': '大专',
        'skill_weight': 50,
        'experience_weight': 30,
        'education_weight': 20,
        'pass_threshold': 70,
        'review_threshold': 50,
        'is_active': True
    },
    {
        'id': UUID('00000000-0000-0000-0000-000000000004'),
        'name': '销售代表',
        'category': 'sales',
        'description': '负责产品销售和客户开发',
        'required_skills': ['销售', '客户开发'],
        'preferred_skills': ['谈判', 'CRM'],
        'min_work_years': 1,
        'min_education': '大专',
        'skill_weight': 50,
        'experience_weight': 30,
        'education_weight': 20,
        'pass_threshold': 70,
        'review_threshold': 50,
        'is_active': True
    }
]

# 初始化预设岗位
for job in preset_jobs:
    jobs_db[str(job['id'])] = job


@router.get("/", response_model=List[JobResponse])
async def list_jobs():
    """获取岗位列表"""
    return [JobResponse(**job) for job in jobs_db.values()]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID):
    """获取岗位详情"""
    job = jobs_db.get(str(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return JobResponse(**job)


@router.post("/", response_model=JobResponse)
async def create_job(job: JobCreate):
    """创建岗位"""
    import uuid
    job_id = uuid.uuid4()
    job_data = job.dict()
    job_data['id'] = job_id
    job_data['is_active'] = True
    jobs_db[str(job_id)] = job_data
    return JobResponse(**job_data)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(job_id: UUID, job_update: JobUpdate):
    """更新岗位"""
    job = jobs_db.get(str(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    update_data = job_update.dict(exclude_unset=True)
    job.update(update_data)
    return JobResponse(**job)


@router.delete("/{job_id}")
async def delete_job(job_id: UUID):
    """删除岗位"""
    job = jobs_db.get(str(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    del jobs_db[str(job_id)]
    return {"message": "岗位已删除"}
