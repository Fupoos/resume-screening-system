"""诊断和修复API

根据CLAUDE.md核心原则：
- 不使用本地JobMatcher
- 所有统��仅基于外部Agent结果
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.models.screening_result import ScreeningResult
from app.models.job import Job
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/matching-stats")
async def get_matching_statistics():
    """获取匹配统计信息

    Returns:
        包含以下信息的字典：
        - total_resumes: 简历总数
        - resumes_with_matches: 有匹配结果的简历数
        - total_screenings: 筛选结果总数
        - job_screening_counts: 每个岗位的筛选结果数
        - recent_screenings: 最近的筛选结果（前5条）
    """
    db = SessionLocal()
    try:
        # 简历总数
        total_resumes = db.query(func.count(Resume.id)).scalar()

        # 有匹配结果的简历数
        resumes_with_matches = db.query(
            func.count(func.distinct(ScreeningResult.resume_id))
        ).scalar()

        # 筛选结果总数
        total_screenings = db.query(func.count(ScreeningResult.id)).scalar()

        # 每个岗位的筛选结果数（从数据库）
        jobs = db.query(Job).filter(Job.is_active == True).all()
        job_screening_counts = {}
        for job in jobs:
            count = db.query(ScreeningResult).filter(
                ScreeningResult.job_id == job.id
            ).count()
            job_screening_counts[job.name] = count

        # 最近的筛选结果（前5条）
        recent_screenings = db.query(ScreeningResult).order_by(
            ScreeningResult.created_at.desc()
        ).limit(5).all()

        screening_details = []
        for sr in recent_screenings:
            resume = db.query(Resume).filter(Resume.id == sr.resume_id).first()
            screening_details.append({
                'resume_id': str(sr.resume_id),
                'candidate_name': resume.candidate_name if resume else 'Unknown',
                'job_id': str(sr.job_id),
                'agent_score': sr.agent_score,
                'screening_result': sr.screening_result,
                'created_at': sr.created_at.isoformat() if sr.created_at else None
            })

        return {
            'total_resumes': total_resumes or 0,
            'resumes_with_matches': resumes_with_matches or 0,
            'resumes_without_matches': (total_resumes or 0) - (resumes_with_matches or 0),
            'total_screenings': total_screenings or 0,
            'job_screening_counts': job_screening_counts,
            'recent_screenings': screening_details
        }
    except Exception as e:
        logger.error(f"获取匹配统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
    finally:
        db.close()


@router.post("/rematch-all")
async def rematch_all_resumes():
    """重新匹配所有简历 - 已废弃

    ⚠️ 此功能已废弃，违反CLAUDE.md核心原则
    所有匹配必须通过外部Agent完成，不能使用本地匹配逻辑

    如需重新匹配，请：
    1. 调用外部Agent服务对简历进行评估
    2. 使用Agent返回的结果更新screening_results表
    """
    raise HTTPException(
        status_code=501,
        detail="此功能已废弃。根据核心原则，所有匹配必须通过外部Agent完成。"
    )


@router.get("/resume/{resume_id}/matches")
async def get_resume_matches(resume_id: str):
    """获取指定简历的匹配结果详情

    Args:
        resume_id: 简历ID

    Returns:
        该简历的所有匹配结果
    """
    db = SessionLocal()
    try:
        # 检查简历是否存在
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="简历不存在")

        # 获取匹配结果
        screenings = db.query(ScreeningResult).filter(
            ScreeningResult.resume_id == resume_id
        ).order_by(ScreeningResult.agent_score.desc().nulls_last()).all()

        # 组合结果（从数据库获取岗位信息）
        results = []
        for sr in screenings:
            # 从数据库获取岗位信息
            job = db.query(Job).filter(Job.id == sr.job_id).first()

            if job:
                results.append({
                    'id': str(sr.id),
                    'job_id': str(sr.job_id),
                    'job_name': job.name,
                    'job_category': job.category,
                    'agent_score': sr.agent_score,
                    'screening_result': sr.screening_result,
                    'matched_points': sr.matched_points or [],
                    'unmatched_points': sr.unmatched_points or [],
                    'suggestion': sr.suggestion,
                    'created_at': sr.created_at.isoformat() if sr.created_at else None
                })

        return {
            'resume_id': resume_id,
            'candidate_name': resume.candidate_name,
            'total_matches': len(results),
            'matches': results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取简历匹配结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
    finally:
        db.close()
