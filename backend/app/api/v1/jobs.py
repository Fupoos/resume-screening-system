"""岗位相关API路由

根据CLAUDE.md核心原则：
- 不使用本��JobMatcher进行匹配
- 岗位信息仅用于展示和传递给外部Agent
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.models.job import Job
from app.core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.on_event("startup")
async def startup_event():
    """应用启动时同步岗位"""
    try:
        from app.tasks.init_jobs_from_agent_config import sync_jobs_from_agent_config
        logger.info("应用启动：开始同步岗位...")
        sync_jobs_from_agent_config()
        logger.info("应用启动：岗位同步完成")
    except Exception as e:
        logger.error(f"应用启动：岗位同步失败 - {e}")
        # 不阻止应用启动，只记录错误


@router.get("/", response_model=List[JobResponse])
async def list_jobs(db: Session = Depends(get_db)):
    """获取岗位列表"""
    jobs = db.query(Job).filter(Job.is_active == True).all()
    return [JobResponse.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, db: Session = Depends(get_db)):
    """获取岗位详情"""
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return JobResponse.model_validate(job)


@router.post("/", response_model=JobResponse)
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """创建岗位"""
    import uuid
    job_id = uuid.uuid4()

    new_job = Job(
        id=job_id,
        **job.dict(),
        is_active=True
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return JobResponse.model_validate(new_job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(job_id: UUID, job_update: JobUpdate, db: Session = Depends(get_db)):
    """更新岗位"""
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    update_data = job_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return JobResponse.model_validate(job)


@router.delete("/{job_id}")
async def delete_job(job_id: UUID, db: Session = Depends(get_db)):
    """删除岗位（软删除）"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 软删除
    job.is_active = False
    db.commit()

    return {"message": "岗位已删除"}
