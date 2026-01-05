"""简历API路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
import os
from datetime import datetime

from app.core.database import get_db
from app.models.resume import Resume
from app.models.screening_result import ScreeningResult
from app.models.job import Job
from app.services.resume_parser import ResumeParser

router = APIRouter()
logger = logging.getLogger(__name__)

# 初始化服务
resume_parser = ResumeParser()

# 文件保存目录
UPLOAD_DIR = "/app/resume_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=dict)
def list_resumes(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(10, ge=1, le=500, description="返回记录数"),
    status: Optional[str] = Query(None, description="筛选状态"),
    file_type: Optional[str] = Query(None, description="筛选文件类型"),
    has_pdf_and_content: bool = Query(False, description="只返回既有PDF文件又有正文的��历"),
    agent_evaluated: Optional[bool] = Query(None, description="只返回已通过Agent评估的简历"),
    min_score: Optional[int] = Query(None, description="最低Agent评分"),
    db: Session = Depends(get_db)
):
    """获取简历列表"""
    query = db.query(Resume)

    if status:
        query = query.filter(Resume.status == status)

    if file_type:
        query = query.filter(Resume.file_type == file_type)

    # 只返回既有PDF又有正文的简历
    if has_pdf_and_content:
        query = query.filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        )

    # 只返回已通过Agent评估的简历
    if agent_evaluated:
        query = query.filter(
            Resume.agent_score.isnot(None),
            Resume.agent_score > 0
        )

    # 最低Agent评分
    if min_score is not None:
        query = query.filter(Resume.agent_score >= min_score)

    total = query.count()

    # 根据是否Agent评估决定排序方式
    if agent_evaluated or min_score is not None:
        resumes = query.order_by(Resume.agent_evaluated_at.desc()).offset(skip).limit(limit).all()
    else:
        resumes = query.order_by(Resume.created_at.desc()).offset(skip).limit(limit).all()

    # 转换为字典格式
    resume_list = []
    for resume in resumes:
        resume_dict = {
            "id": str(resume.id),
            "candidate_name": resume.candidate_name,
            "phone": resume.phone,
            "email": resume.email,
            "education": resume.education,
            "education_level": resume.education_level,
            "work_years": resume.work_years,
            "skills": resume.skills or [],
            "skills_by_level": resume.skills_by_level,
            "status": resume.status,
            "file_type": resume.file_type,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
            # Agent相关字段
            "city": resume.city,
            "job_category": resume.job_category,
            "agent_score": resume.agent_score,
            "agent_evaluation_id": resume.agent_evaluation_id,
            "screening_status": resume.screening_status,
            "agent_evaluated_at": resume.agent_evaluated_at.isoformat() if resume.agent_evaluated_at else None,
            "work_experience": resume.work_experience  # 🔴 新增：工作经历
        }
        resume_list.append(resume_dict)

    return {
        "total": total,
        "items": resume_list,
        "page": skip // limit + 1 if limit else 1,
        "page_size": limit
    }


@router.get("/{resume_id}", response_model=dict)
def get_resume(resume_id: UUID, db: Session = Depends(get_db)):
    """获取简历详情"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()

    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    return {
        "id": str(resume.id),
        "candidate_name": resume.candidate_name,
        "phone": resume.phone,
        "email": resume.email,
        "education": resume.education,
        "education_level": resume.education_level,
        "work_years": resume.work_years,
        "skills": resume.skills or [],
        "skills_by_level": resume.skills_by_level,  # 新增
        "work_experience": resume.work_experience or [],
        "project_experience": resume.project_experience or [],
        "education_history": resume.education_history or [],
        "raw_text": resume.raw_text,
        "file_path": resume.file_path,
        "file_type": resume.file_type,
        "source_email_id": resume.source_email_id,
        "source_email_subject": resume.source_email_subject,
        "source_sender": resume.source_sender,
        "status": resume.status,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
        "updated_at": resume.updated_at.isoformat() if resume.updated_at else None
    }


@router.post("/upload", response_model=dict)
async def upload_resume(
    file: UploadFile = File(..., description="简历文件(PDF/DOCX)"),
    auto_match: bool = Query(True, description="是否自动匹配岗位"),
    db: Session = Depends(get_db)
):
    """手动上传简历并自动匹配

    Args:
        file: 简历文件（PDF或DOCX）
        auto_match: 是否自动匹配所有岗位
    """
    try:
        # 1. 保存文件
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['pdf', 'docx', 'doc']:
            raise HTTPException(status_code=400, detail="仅支持PDF和DOCX格式")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 2. 解析简历
        logger.info(f"开始解析简历: {file_path}")
        resume_data = resume_parser.parse_resume(file_path)

        # 如果仍然没有提取到姓名，尝试从原始文件名提取
        if not resume_data.get('candidate_name'):
            candidate_name_from_filename = resume_parser._extract_name_from_filename(file.filename)
            candidate_name = candidate_name_from_filename or Path(file.filename).stem
        else:
            candidate_name = resume_data.get('candidate_name')

        # 3. 保存到数据库
        resume = Resume(
            candidate_name=candidate_name,
            phone=resume_data.get('phone'),
            email=resume_data.get('email'),
            education=resume_data.get('education'),
            work_years=resume_data.get('work_years', 0),
            skills=resume_data.get('skills', []),
            work_experience=resume_data.get('work_experience', []),
            project_experience=resume_data.get('project_experience', []),
            education_history=resume_data.get('education_history', []),
            raw_text=resume_data.get('raw_text'),
            file_path=file_path,
            file_type=file_ext,
            status='parsed'
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        logger.info(f"简历已保存: {resume.id}, 候选人: {resume.candidate_name}")

        # 4. ❌ 已删除本地自动匹配功能（违反CLAUDE.md核心原则）
        # 根据核心原则：所有评分必须通过外部Agent完成
        # 如果需要自动评估，应该调用外部Agent服务

        return {
            "resume_id": str(resume.id),
            "message": "简历上传成功，等待外部Agent评估"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传简历失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.delete("/{resume_id}", response_model=dict)
def delete_resume(resume_id: UUID, db: Session = Depends(get_db)):
    """删除简历"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()

    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 删除关联的筛选结果
    db.query(ScreeningResult).filter(ScreeningResult.resume_id == resume_id).delete()

    # 删除简历文件
    if resume.file_path and os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception as e:
            logger.warning(f"删除文件失败: {resume.file_path}, 错误: {str(e)}")

    # 删除数据库记录
    db.delete(resume)
    db.commit()

    return {"message": "简历已删除"}


@router.get("/{resume_id}/screenings", response_model=dict)
def get_resume_screenings(
    resume_id: UUID,
    db: Session = Depends(get_db)
):
    """获取简历的筛选结果（前2个最佳匹配）"""
    # 检查简历是否存在
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 获取筛选结果，按分数降序，取前2个
    screenings = db.query(ScreeningResult).filter(
        ScreeningResult.resume_id == resume_id
    ).order_by(ScreeningResult.agent_score.desc().nulls_last()).limit(2).all()

    results = []
    for screening in screenings:
        # 找到对应的岗位信息（从数据库）
        job = db.query(Job).filter(Job.id == screening.job_id).first()

        results.append({
            "id": str(screening.id),
            "job_id": str(screening.job_id),
            "job_name": job.name if job else "未知岗位",
            "job_category": job.category if job else "unknown",
            "agent_score": screening.agent_score,
            "screening_result": screening.screening_result,
            "matched_points": screening.matched_points or [],
            "unmatched_points": screening.unmatched_points or [],
            "suggestion": screening.suggestion,
            "created_at": screening.created_at.isoformat() if screening.created_at else None
        })

    return {
        "resume_id": str(resume_id),
        "candidate_name": resume.candidate_name,
        "total_matches": len(results),
        "matches": results
    }
