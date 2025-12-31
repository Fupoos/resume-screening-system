"""筛选相关API路由"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.screening_result import ScreeningResult
from app.models.resume import Resume
from app.api.v1.jobs import preset_jobs

router = APIRouter()


@router.post("/match")
async def match_resume(request: dict, db: Session = Depends(get_db)):
    """匹配简历与岗位（手动匹配，不保存到数据库）"""
    from app.services.job_matcher import JobMatcher
    from app.schemas.screening import MatchRequest

    job_matcher = JobMatcher()

    # 查找岗位
    job = None
    for j in preset_jobs:
        if str(j.id) == str(request.get('job_id')):
            job = j
            break

    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 构建简历数据
    resume = {
        'candidate_name': request.get('candidate_name'),
        'phone': request.get('phone'),
        'email': request.get('email'),
        'education': request.get('education'),
        'work_years': request.get('work_years') or 0,
        'skills': request.get('skills', [])
    }

    # 执行匹配
    result = job_matcher.match(resume, job.__dict__)

    return {
        'candidate_name': request.get('candidate_name'),
        'job_name': job.name,
        'screening_result': result['screening_result'],
        'match_score': result['match_score'],
        'skill_score': result['skill_score'],
        'experience_score': result['experience_score'],
        'education_score': result['education_score'],
        'matched_points': result['matched_points'],
        'unmatched_points': result['unmatched_points'],
        'suggestion': result['suggestion']
    }


@router.get("/results")
async def list_screening_results(
    resume_id: Optional[UUID] = Query(None, description="筛选简历ID"),
    job_id: Optional[UUID] = Query(None, description="筛选岗位ID"),
    result: Optional[str] = Query(None, description="筛选结果类型"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db)
):
    """获取筛选结果列表（返回所有有正文内容的简历的筛选结果）"""
    # 构建查询
    query = db.query(ScreeningResult)

    if resume_id:
        query = query.filter(ScreeningResult.resume_id == resume_id)
    if job_id:
        query = query.filter(ScreeningResult.job_id == job_id)
    if result:
        query = query.filter(ScreeningResult.screening_result == result.upper())

    # 只获取有PDF且有正文内容的简历的筛选结果
    valid_resume_ids = db.query(Resume.id).filter(
        Resume.file_type == 'pdf',
        Resume.raw_text.isnot(None),
        Resume.raw_text != ''
    ).all()

    valid_resume_ids_list = [r.id for r in valid_resume_ids]

    # 过滤筛选结果
    query = query.filter(ScreeningResult.resume_id.in_(valid_resume_ids_list))

    # 获取所有筛选结果
    all_screenings = query.order_by(ScreeningResult.created_at.desc()).all()

    # 过滤掉明显异常的简历名字
    import re
    def is_valid_name(name: str) -> bool:
        """检查名字是否有效（放宽条件）"""
        if not name:
            return False

        # 排除明显的无效名字
        invalid_patterns = [
            r'^[0-9a-fA-F-]{36}$',  # UUID格式
            r'^实习|工作|项目|教育|技能|求职|个人|基本信息|联系方式',  # 常见标题
            r'^双一流|211|985|学士|硕士|博士|本科|大专|高中|中专',  # 学历相关
        ]
        for pattern in invalid_patterns:
            if re.search(pattern, name):
                return False

        # 长度检查：放宽到1-10个字符
        if len(name) < 1 or len(name) > 10:
            return False

        # 排除纯英文（但保留中英混合）
        if re.match(r'^[a-zA-Z\s]+$', name):
            return False

        return True

    # 获取所有有名字的简历
    valid_resume_with_names = db.query(Resume.id).filter(
        Resume.id.in_(valid_resume_ids_list),
        Resume.candidate_name.isnot(None),
        Resume.candidate_name != ''
    ).all()

    # 构建有效简历ID集合（名字正常的）
    valid_resume_ids_clean = []
    for r in valid_resume_with_names:
        resume = db.query(Resume).filter(Resume.id == r.id).first()
        if resume and is_valid_name(resume.candidate_name):
            valid_resume_ids_clean.append(r.id)

    # 再次过滤筛选结果，只保留名字正常的
    all_screenings = [s for s in all_screenings if s.resume_id in valid_resume_ids_clean]

    # 按简历分组，取前2个最佳匹配
    resume_groups = {}
    for screening in all_screenings:
        rid = str(screening.resume_id)
        if rid not in resume_groups:
            resume_groups[rid] = []
        resume_groups[rid].append(screening)

    # 每个简历只保留前2个最佳匹配
    for rid in resume_groups:
        resume_groups[rid].sort(key=lambda x: x.match_score, reverse=True)
        resume_groups[rid] = resume_groups[rid][:2]

    # 展平并分页
    flat_results = []
    for screenings in resume_groups.values():
        flat_results.extend(screenings)

    total = len(flat_results)
    paginated_results = flat_results[skip:skip + limit]

    # 转换为响应格式
    results = []
    for screening in paginated_results:
        # 获取简历信息
        resume = db.query(Resume).filter(Resume.id == screening.resume_id).first()

        # 获取岗位信息
        job = None
        for j in preset_jobs:
            if str(j['id']) == str(screening.job_id):
                job = j
                break

        results.append({
            "id": str(screening.id),
            "resume_id": str(screening.resume_id),
            "candidate_name": resume.candidate_name if resume else "未知",
            "candidate_email": resume.email if resume else None,
            "candidate_phone": resume.phone if resume else None,
            "candidate_education": resume.education if resume else None,
            "job_id": str(screening.job_id),
            "job_name": job['name'] if job else "未知岗位",
            "job_category": job['category'] if job else "unknown",
            "match_score": screening.match_score,
            "skill_score": screening.skill_score,
            "experience_score": screening.experience_score,
            "education_score": screening.education_score,
            "screening_result": screening.screening_result,
            "matched_points": screening.matched_points or [],
            "unmatched_points": screening.unmatched_points or [],
            "suggestion": screening.suggestion,
            "created_at": screening.created_at.isoformat() if screening.created_at else None
        })

    return {
        "total": total,
        "results": results
    }


@router.get("/result/{screening_id}")
async def get_screening_result(screening_id: UUID, db: Session = Depends(get_db)):
    """获取筛选结果详情"""
    screening = db.query(ScreeningResult).filter(ScreeningResult.id == screening_id).first()

    if not screening:
        raise HTTPException(status_code=404, detail="筛选结果不存在")

    # 获取简历信息
    resume = db.query(Resume).filter(Resume.id == screening.resume_id).first()

    # 获取岗位信息
    job = None
    for j in preset_jobs:
        if str(j.id) == str(screening.job_id):
            job = j
            break

    return {
        "id": str(screening.id),
        "resume_id": str(screening.resume_id),
        "candidate_name": resume.candidate_name if resume else "未知",
        "candidate_email": resume.email if resume else None,
        "candidate_phone": resume.phone if resume else None,
        "candidate_education": resume.education if resume else None,
        "candidate_work_years": resume.work_years if resume else None,
        "candidate_skills": resume.skills if resume else [],
        "job_id": str(screening.job_id),
        "job_name": job.name if job else "未知岗位",
        "job_category": job.category if job else "unknown",
        "match_score": screening.match_score,
        "skill_score": screening.skill_score,
        "experience_score": screening.experience_score,
        "education_score": screening.education_score,
        "screening_result": screening.screening_result,
        "matched_points": screening.matched_points or [],
        "unmatched_points": screening.unmatched_points or [],
        "suggestion": screening.suggestion,
        "created_at": screening.created_at.isoformat() if screening.created_at else None
    }
