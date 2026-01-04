"""诊断和修复API

根据CLAUDE.md核心原则：
- 不使用本地JobMatcher
- 所有统计仅基于外部Agent结果
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.models.screening_result import ScreeningResult
from app.api.v1.jobs import preset_jobs
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

        # 每个岗位的筛选结果数
        job_screening_counts = {}
        for job in preset_jobs:
            count = db.query(ScreeningResult).filter(
                ScreeningResult.job_id == str(job['id'])
            ).count()
            job_screening_counts[job['name']] = count

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
                'match_score': sr.match_score,
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
    """重新匹配所有简历

    删除所有现有的筛选结果，为每份简历重新匹配所有岗位并保存前2名。

    Returns:
        包含处理结果的字典：
        - total: 简历总数
        - processed: 成功处理的简历数
        - failed: 失败的简历数
        - errors: 错误列表
    """
    db = SessionLocal()
    try:
        # 获取所有简历
        resumes = db.query(Resume).all()

        if not resumes:
            return {
                'total': 0,
                'processed': 0,
                'failed': 0,
                'errors': [],
                'message': '没有简历需要处理'
            }

        results = {
            'total': len(resumes),
            'processed': 0,
            'failed': 0,
            'errors': []
        }

        job_matcher = JobMatcher()
        logger.info(f"开始重新匹配 {len(resumes)} 份简历")

        for resume in resumes:
            try:
                # 删除旧的筛选结果
                deleted_count = db.query(ScreeningResult).filter(
                    ScreeningResult.resume_id == resume.id
                ).delete()
                logger.info(
                    f"简历 {resume.candidate_name} (ID: {resume.id}): "
                    f"删除 {deleted_count} 条旧匹配结果"
                )

                # 构建简历数据
                resume_dict = {
                    'candidate_name': resume.candidate_name,
                    'phone': resume.phone,
                    'email': resume.email,
                    'education': resume.education,
                    'work_years': resume.work_years or 0,
                    'skills': resume.skills or []
                }

                # 重新匹配（取前2名）
                top_matches = job_matcher.auto_match_resume(
                    resume=resume_dict,
                    jobs=preset_jobs,
                    top_n=2
                )

                # 保存新的筛选结果
                for match in top_matches:
                    screening = ScreeningResult(
                        resume_id=resume.id,
                        job_id=match['job_id'],
                        match_score=match['match_score'],
                        skill_score=match['skill_score'],
                        experience_score=match['experience_score'],
                        education_score=match['education_score'],
                        matched_points=match['matched_points'],
                        unmatched_points=match['unmatched_points'],
                        screening_result=match['screening_result'],
                        suggestion=match['suggestion']
                    )
                    db.add(screening)

                db.commit()
                results['processed'] += 1
                logger.info(
                    f"简历 {resume.candidate_name} 重新匹配成功， "
                    f"保存了 {len(top_matches)} 个匹配结果"
                )

            except Exception as e:
                db.rollback()
                results['failed'] += 1
                error_msg = {
                    'resume_id': str(resume.id),
                    'candidate_name': resume.candidate_name,
                    'error': str(e)
                }
                results['errors'].append(error_msg)
                logger.error(f"处理简历 {resume.id} 失败: {e}")

        logger.info(
            f"重新匹配完成: 总计 {results['total']} 份简历, "
            f"成功 {results['processed']} 份, 失败 {results['failed']} 份"
        )

        return results

    except Exception as e:
        logger.error(f"重新匹配过程出错: {e}")
        raise HTTPException(status_code=500, detail=f"重新匹配失败: {str(e)}")
    finally:
        db.close()


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
        ).order_by(ScreeningResult.match_score.desc()).all()

        # 组合结果
        results = []
        for sr in screenings:
            # 找到对应的岗位
            job = None
            for j in preset_jobs:
                if str(j['id']) == str(sr.job_id):
                    job = j
                    break

            if job:
                results.append({
                    'id': str(sr.id),
                    'job_id': str(sr.job_id),
                    'job_name': job['name'],
                    'job_category': job['category'],
                    'match_score': sr.match_score,
                    'skill_score': sr.skill_score,
                    'experience_score': sr.experience_score,
                    'education_score': sr.education_score,
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
