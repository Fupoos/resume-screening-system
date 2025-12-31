"""数据清理API路由 - 用于清理和重新计算工作年限等数据"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, Any
from datetime import datetime
import logging

from app.core.database import get_db, SessionLocal
from app.models.resume import Resume
from app.models.screening_result import ScreeningResult
from app.services.resume_parser import ResumeParser
from app.services.job_matcher import JobMatcher
from app.api.v1.jobs import preset_jobs

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/work-years-stats")
async def get_work_years_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取工作年限数据统计

    返回：
    - total: 总记录数
    - null_count: NULL值数量
    - zero_count: 0值数量
    - year_value_count: 年份值数量（>200，明显异常）
    - normal_count: 正常值数量（1-50年）
    - distribution: 分段分布
    """
    # 总记录数
    total = db.query(func.count(Resume.id)).scalar()

    # NULL值数量
    null_count = db.query(func.count(Resume.id)).filter(
        Resume.work_years.is_(None)
    ).scalar()

    # 0值数量
    zero_count = db.query(func.count(Resume.id)).filter(
        Resume.work_years == 0
    ).scalar()

    # 年份值数量（>200，明显异常）
    year_value_count = db.query(func.count(Resume.id)).filter(
        Resume.work_years > 200
    ).scalar()

    # 正常值数量（1-50年）
    normal_count = db.query(func.count(Resume.id)).filter(
        and_(
            Resume.work_years >= 1,
            Resume.work_years <= 50
        )
    ).scalar()

    # 分段分布
    distribution = {
        "0年": zero_count,
        "1-3年": db.query(func.count(Resume.id)).filter(
            and_(
                Resume.work_years >= 1,
                Resume.work_years <= 3
            )
        ).scalar(),
        "4-6年": db.query(func.count(Resume.id)).filter(
            and_(
                Resume.work_years >= 4,
                Resume.work_years <= 6
            )
        ).scalar(),
        "7-10年": db.query(func.count(Resume.id)).filter(
            and_(
                Resume.work_years >= 7,
                Resume.work_years <= 10
            )
        ).scalar(),
        "11-20年": db.query(func.count(Resume.id)).filter(
            and_(
                Resume.work_years >= 11,
                Resume.work_years <= 20
            )
        ).scalar(),
        "20年以上": db.query(func.count(Resume.id)).filter(
            Resume.work_years > 20
        ).scalar(),
    }

    return {
        "total": total,
        "null_count": null_count,
        "zero_count": zero_count,
        "year_value_count": year_value_count,
        "normal_count": normal_count,
        "distribution": distribution,
        "quality_percentage": round((normal_count / total * 100) if total > 0 else 0, 2)
    }


@router.post("/recalculate-all-work-years")
async def recalculate_all_work_years(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """重新计算所有简历的工作年限

    处理范围：所有有PDF且有正文的简历

    返回：
    - total: 总处理数量
    - success: 成功数量
    - failed: 失败数量
    - errors: 错误详情（最多10条）
    """
    return recalculate_all_work_years_impl(db)


@router.post("/fix-year-value-anomalies")
async def fix_year_value_anomalies(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """修复所有异常的work_years值（负数、>50、>200等）

    将这些异常值重新计算为正确的工作年限

    返回：
    - total: 总处理数量
    - fixed: 修复数量
    - failed: 失败数量
    - details: 详细信息
    """
    from sqlalchemy import or_

    # 查询所有异常的work_years：负数、>50、>200
    anomalies = db.query(Resume).filter(
        or_(
            Resume.work_years < 0,
            Resume.work_years > 50
        )
    ).all()

    total = len(anomalies)
    fixed = 0
    failed = 0
    errors = []

    parser = ResumeParser()

    for resume in anomalies:
        try:
            # 只有有raw_text的才能重新计算
            if not resume.raw_text or len(resume.raw_text) < 50:
                failed += 1
                errors.append({
                    "resume_id": str(resume.id),
                    "candidate_name": resume.candidate_name,
                    "error": "raw_text为空或太短"
                })
                continue

            # 重新解析工作经历
            work_experience = parser._extract_work_experience(resume.raw_text)

            # 计算工作年限
            work_years = parser._calculate_work_years(work_experience)

            # 更新数据库
            old_value = resume.work_years
            resume.work_years = work_years
            resume.work_experience = work_experience

            fixed += 1

            logger.info(
                f"修复异常值: {resume.candidate_name} "
                f"work_years从 {old_value} 改为 {work_years}"
            )

        except Exception as e:
            failed += 1
            error_detail = {
                "resume_id": str(resume.id),
                "candidate_name": resume.candidate_name,
                "old_work_years": resume.work_years,
                "error": str(e)
            }
            errors.append(error_detail)
            logger.error(f"修复简历 {resume.id} 失败: {e}")

    # 提交所有更改
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库提交失败: {str(e)}")

    return {
        "total": total,
        "fixed": fixed,
        "failed": failed,
        "errors": errors[:10],  # 只返回前10条错误
        "message": f"已处理 {total} 份异常简历，成功修复 {fixed} 份，失败 {failed} 份"
    }


@router.post("/cleanup-and-rematch")
async def cleanup_and_rematch(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """完整流程：清理工作年限 + 删除旧筛选结果 + 重新匹配

    返回：
    - step1: 工作年限清理结果
    - step2: 删除旧筛选结果
    - step3: 重新匹配结果
    """
    result = {}

    # ========== 步骤1: 重新计算工作年限 ==========
    try:
        # 调用同步函数（不使用await）
        cleanup_result = recalculate_all_work_years_impl(db)
        result["step1"] = {
            "status": "success",
            "message": cleanup_result["message"],
            "details": {
                "total": cleanup_result["total"],
                "success": cleanup_result["success"],
                "failed": cleanup_result["failed"]
            }
        }
    except Exception as e:
        result["step1"] = {
            "status": "failed",
            "error": str(e)
        }
        raise HTTPException(status_code=500, detail=f"步骤1失败: {str(e)}")

    # ========== 步骤2: 删除所有旧筛选结果 ==========
    try:
        deleted_count = db.query(ScreeningResult).delete()
        db.commit()
        result["step2"] = {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"已删除 {deleted_count} 条旧筛选结果"
        }
    except Exception as e:
        db.rollback()
        result["step2"] = {
            "status": "failed",
            "error": str(e)
        }
        raise HTTPException(status_code=500, detail=f"步骤2失败: {str(e)}")

    # ========== 步骤3: 重新匹配所有简历 ==========
    try:
        match_result = rematch_all_resumes_impl(db)
        result["step3"] = {
            "status": "success",
            "message": f"已重新匹配 {match_result.get('total', 0)} 份简历",
            "details": match_result
        }
    except Exception as e:
        result["step3"] = {
            "status": "failed",
            "error": str(e)
        }
        # 不抛出异常，因为前两步已经成功

    result["summary"] = {
        "status": "complete",
        "message": "数据清理和重新匹配完成"
    }

    return result


# ========== 辅助函数（同步实现） ==========

def recalculate_all_work_years_impl(db: Session) -> Dict[str, Any]:
    """重新计算工作年限的同步实现"""
    # 查找所有有PDF且有正文的简历
    resumes = db.query(Resume).filter(
        and_(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        )
    ).all()

    total = len(resumes)
    success = 0
    failed = 0
    errors = []

    parser = ResumeParser()

    for resume in resumes:
        try:
            # 从raw_text重新解析工作年限
            if not resume.raw_text:
                failed += 1
                errors.append({
                    "resume_id": str(resume.id),
                    "candidate_name": resume.candidate_name,
                    "error": "raw_text为空"
                })
                continue

            # 重新解析工作经历
            work_experience = parser._extract_work_experience(resume.raw_text)

            # 计算工作年限
            work_years = parser._calculate_work_years(work_experience)

            # 更新数据库
            resume.work_years = work_years
            resume.work_experience = work_experience

            success += 1

        except Exception as e:
            failed += 1
            error_detail = {
                "resume_id": str(resume.id),
                "candidate_name": resume.candidate_name,
                "error": str(e)
            }
            errors.append(error_detail)
            if len(errors) >= 10:
                errors.append(f"... (还有 {failed - len(errors)} 条错误)")
                break

    # 提交所有更改
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库提交失败: {str(e)}")

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "errors": errors[:10],
        "message": f"已处理 {total} 份简历，成功 {success} 份，失败 {failed} 份"
    }


def rematch_all_resumes_impl(db: Session) -> Dict[str, Any]:
    """重新匹配所有简历的同步实现"""
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

