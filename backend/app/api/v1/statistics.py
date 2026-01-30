"""统计API - 提供简历筛选的统计分析功能"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy import func, case, and_
from app.core.database import SessionLocal, get_db
from app.core.auth import get_current_user
from app.models.resume import Resume
from app.models.screening_result import ScreeningResult
from app.models.job import Job
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取Dashboard综合统计数据（根据用户权限过滤）

    🔴 只统计已配置FastGPT Agent的岗位类别（与筛选结果页面保持一致）
    🔴 非管理员用户只统计有权限的岗位类别

    统计规则基于resume.agent_score字段（与筛选结果页面保持一致）：
    - 70-100分：可以发offer
    - 40-70分：待定
    - 0-40分：不合格

    Returns:
        {
            "overview": {
                "total_resumes": int,      # 总简历数（有效简历）
                "evaluated_count": int,    # 已评估数量
                "pending_count": int,      # 待评估数量
                "pass_count": int,         # 可以发offer数量
                "review_count": int,       # 待定数量
                "reject_count": int,       # 不合格数量
                "pass_rate": float,        # 通过率（基于已评估）
                "avg_score": float         # 平均分（基于已评估）
            }
        }
    """
    db = SessionLocal()
    try:
        # 🔴 获取已配置FastGPT Agent的岗位名称（与筛选结果页面保持一致）
        agent_jobs = db.query(Job).filter(
            Job.is_active == True,
            Job.agent_type == 'fastgpt'
        ).all()
        agent_job_names = set(job.name for job in agent_jobs)

        # 权限过滤：管理员看全部，HR用户只看有权限的岗位
        if current_user.role != "admin":
            from app.models.user import UserJobCategory
            accessible_categories = db.query(UserJobCategory.job_category_name).filter(
                UserJobCategory.user_id == current_user.id
            ).all()
            user_accessible_names = set(cat[0] for cat in accessible_categories)
            # 取交集
            agent_job_names = agent_job_names & user_accessible_names

        if not agent_job_names:
            # 用户无权限，返回空统计
            return {
                "overview": {
                    "total_resumes": 0,
                    "evaluated_count": 0,
                    "pending_count": 0,
                    "pass_count": 0,
                    "review_count": 0,
                    "reject_count": 0,
                    "pass_rate": 0,
                    "avg_score": 0
                }
            }

        # 🔴 统计所有有效简历（与筛选结果页面保持一致）
        # 有效简历定义：PDF/DOCX + 有raw_text + job_category在FastGPT岗位中
        base_filters = [
            Resume.job_category.in_(agent_job_names),
            Resume.file_type.in_(['pdf', 'docx']),
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ]

        # 总简历数（所有有效简历）
        total = db.query(func.count(Resume.id)).filter(*base_filters).scalar()

        # 已评估数量（有agent_score的简历）
        evaluated_count = db.query(func.count(Resume.id)).filter(
            *base_filters,
            Resume.agent_score.isnot(None)
        ).scalar()

        # 待评估数量
        pending_count = (total or 0) - (evaluated_count or 0)

        # 可以发offer数量 (agent_score >= 70)
        pass_count = db.query(func.count(Resume.id)).filter(
            *base_filters,
            Resume.agent_score >= 70
        ).scalar()

        # 待定数量 (40 <= agent_score < 70)
        review_count = db.query(func.count(Resume.id)).filter(
            *base_filters,
            Resume.agent_score >= 40,
            Resume.agent_score < 70
        ).scalar()

        # 不合格数量 (agent_score < 40)
        reject_count = db.query(func.count(Resume.id)).filter(
            *base_filters,
            Resume.agent_score < 40
        ).scalar()

        # 平均分（只计算已评估的）
        avg_score = db.query(func.avg(Resume.agent_score)).filter(
            *base_filters,
            Resume.agent_score.isnot(None)
        ).scalar()

        return {
            "overview": {
                "total_resumes": total or 0,
                "evaluated_count": evaluated_count or 0,
                "pending_count": pending_count,
                "pass_count": pass_count or 0,
                "review_count": review_count or 0,
                "reject_count": reject_count or 0,
                "pass_rate": round((pass_count / evaluated_count), 3) if evaluated_count and evaluated_count > 0 else 0,
                "avg_score": round(float(avg_score), 2) if avg_score else 0
            }
        }
    except Exception as e:
        logger.error(f"获取Dashboard统计失败: {str(e)}")
        return {
            "overview": {
                "total_resumes": 0,
                "pass_count": 0,
                "review_count": 0,
                "reject_count": 0,
                "pass_rate": 0,
                "avg_score": 0
            }
        }
    finally:
        db.close()


@router.get("/by-city")
async def get_statistics_by_city(
    current_user: User = Depends(get_current_user)
):
    """按城市统计（根据用户权限过滤）

    🔴 只统计已配置FastGPT Agent的岗位类别（与筛选结果页面保持一致）
    🔴 非管理员用户只统计有权限的岗位类别

    使用resume.agent_score字段进行统计（与筛选结果页面保持一致）：
    - 70-100分：可以发offer
    - 40-70分：待定
    - 0-40分：不合格

    Returns:
        {
            "北京": {
                "total": int,
                "pass": int,
                "review": int,
                "reject": int,
                "avg_score": float,
                "pass_rate": float
            },
            ...
        }
    """
    db = SessionLocal()
    try:
        # 🔴 获取已配置FastGPT Agent的岗位名称（与筛选结果页面保持一致）
        agent_jobs = db.query(Job).filter(
            Job.is_active == True,
            Job.agent_type == 'fastgpt'
        ).all()
        agent_job_names = set(job.name for job in agent_jobs)

        # 权限过滤：管理员看全部，HR用户只看有权限的岗位
        if current_user.role != "admin":
            from app.models.user import UserJobCategory
            accessible_categories = db.query(UserJobCategory.job_category_name).filter(
                UserJobCategory.user_id == current_user.id
            ).all()
            user_accessible_names = set(cat[0] for cat in accessible_categories)
            agent_job_names = agent_job_names & user_accessible_names

        if not agent_job_names:
            return {}

        # 🔴 统计所有有效简历（基于resume.agent_score）
        base_filters = [
            Resume.job_category.in_(agent_job_names),
            Resume.file_type.in_(['pdf', 'docx']),
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ]

        # 按城市统计
        query = db.query(
            Resume.city,
            func.count(Resume.id).label('total'),
            func.sum(case((Resume.agent_score >= 70, 1), else_=0)).label('pass'),
            func.sum(case((and_(Resume.agent_score >= 40, Resume.agent_score < 70), 1), else_=0)).label('review'),
            func.sum(case((Resume.agent_score < 40, 1), else_=0)).label('reject'),
            func.avg(Resume.agent_score).label('avg_score')
        ).filter(
            *base_filters
        ).group_by(Resume.city)

        results = query.all()

        return {
            (r[0] or "未知"): {
                "total": r[1],
                "pass": int(r[2]) if r[2] else 0,
                "review": int(r[3]) if r[3] else 0,
                "reject": int(r[4]) if r[4] else 0,
                "avg_score": round(float(r[5]), 2) if r[5] else 0,
                "pass_rate": round((int(r[2]) / r[1]), 3) if r[1] and r[1] > 0 else 0
            }
            for r in results
        }
    except Exception as e:
        logger.error(f"获取城市统计失败: {str(e)}")
        return {}
    finally:
        db.close()


@router.get("/by-job")
async def get_statistics_by_job(
    current_user: User = Depends(get_current_user)
):
    """按具体职位统计（根据用户权限过滤）

    🔴 只统计已配置FastGPT Agent的岗位类别（与筛选结果页面保持一致）
    🔴 非管理员用户只统计有权限的岗位类别

    使用resume.agent_score字段进行统计（与筛选结果页面保持一致）：
    - 70-100分：可以发offer
    - 40-70分：待定
    - 0-40分：不合格

    Returns:
        {
            "Java开发": {
                "total": int,
                "pass": int,
                "review": int,
                "reject": int,
                "avg_score": float
            },
            ...
        }
    """
    db = SessionLocal()
    try:
        # 🔴 获取已配置FastGPT Agent的岗位名称（与筛选结果页面保持一致）
        agent_jobs = db.query(Job).filter(
            Job.is_active == True,
            Job.agent_type == 'fastgpt'
        ).all()
        agent_job_names = set(job.name for job in agent_jobs)

        # 权限过滤：管理员看全部，HR用户只看有权限的岗位
        if current_user.role != "admin":
            from app.models.user import UserJobCategory
            accessible_categories = db.query(UserJobCategory.job_category_name).filter(
                UserJobCategory.user_id == current_user.id
            ).all()
            user_accessible_names = set(cat[0] for cat in accessible_categories)
            agent_job_names = agent_job_names & user_accessible_names

        if not agent_job_names:
            return {}

        # 🔴 统计所有有效简历（基于resume.agent_score）
        base_filters = [
            Resume.job_category.in_(agent_job_names),
            Resume.file_type.in_(['pdf', 'docx']),
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ]

        # 按职位统计
        query = db.query(
            Resume.job_category,
            func.count(Resume.id).label('total'),
            func.sum(case((Resume.agent_score >= 70, 1), else_=0)).label('pass'),
            func.sum(case((and_(Resume.agent_score >= 40, Resume.agent_score < 70), 1), else_=0)).label('review'),
            func.sum(case((Resume.agent_score < 40, 1), else_=0)).label('reject'),
            func.avg(Resume.agent_score).label('avg_score')
        ).filter(
            *base_filters
        ).group_by(Resume.job_category)

        results = query.all()

        return {
            (r[0] or "待分类"): {
                "total": r[1],
                "pass": int(r[2]) if r[2] else 0,
                "review": int(r[3]) if r[3] else 0,
                "reject": int(r[4]) if r[4] else 0,
                "avg_score": round(float(r[5]), 2) if r[5] else 0
            }
            for r in results
        }
    except Exception as e:
        logger.error(f"获取职位统计失败: {str(e)}")
        return {}
    finally:
        db.close()


@router.get("/by-time")
async def get_statistics_by_time(
    start: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end: str = Query(..., description="结束日期 YYYY-MM-DD"),
    group_by: str = Query("day", description="分组方式: day/week/month"),
    current_user: User = Depends(get_current_user)
):
    """按时间段统计（根据用户权限过滤）

    🔴 只统计已配置FastGPT Agent的岗位类别（与筛选结果页面保持一致）
    🔴 非管理员用户只统计有权限的岗位类别

    Args:
        start: 开始日期 (YYYY-MM-DD)
        end: 结束日期 (YYYY-MM-DD)
        group_by: 分组方式 (day/week/month)

    Returns:
        {
            "2025-01-01": {
                "total": int,
                "pass": int,
                "review": int,
                "reject": int,
                "avg_score": float
            },
            ...
        }
    """
    from datetime import datetime

    db = SessionLocal()
    try:
        # 🔴 获取已配置FastGPT Agent的岗位名称（与筛选结果页面保持一致）
        agent_jobs = db.query(Job).filter(
            Job.is_active == True,
            Job.agent_type == 'fastgpt'
        ).all()
        agent_job_names = set(job.name for job in agent_jobs)

        # 权限过滤：管理员看全部，HR用户只看有权限的岗位
        if current_user.role != "admin":
            from app.models.user import UserJobCategory
            accessible_categories = db.query(UserJobCategory.job_category_name).filter(
                UserJobCategory.user_id == current_user.id
            ).all()
            user_accessible_names = set(cat[0] for cat in accessible_categories)
            agent_job_names = agent_job_names & user_accessible_names

        if not agent_job_names:
            return {}

        # 解析日期
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        # 根据group_by选择时间格式
        if group_by == "day":
            date_format = func.date_trunc('day', Resume.created_at)
            date_label = func.to_char(Resume.created_at, 'YYYY-MM-DD')
        elif group_by == "week":
            date_format = func.date_trunc('week', Resume.created_at)
            date_label = func.to_char(Resume.created_at, 'IYYY-"W"IW')
        elif group_by == "month":
            date_format = func.date_trunc('month', Resume.created_at)
            date_label = func.to_char(Resume.created_at, 'YYYY-MM')
        else:
            date_format = func.date_trunc('day', Resume.created_at)
            date_label = func.to_char(Resume.created_at, 'YYYY-MM-DD')

        # 🔴 查询统计数据（只统计FastGPT岗位）
        results = db.query(
            date_label.label('date'),
            func.count(Resume.id).label('total'),
            func.sum(case((Resume.screening_status == '可以发offer', 1), else_=0)).label('pass'),
            func.sum(case((Resume.screening_status == '待定', 1), else_=0)).label('review'),
            func.sum(case((Resume.screening_status == '不合格', 1), else_=0)).label('reject'),
            func.avg(Resume.agent_score).label('avg_score')
        ).filter(
            Resume.created_at >= start_date,
            Resume.created_at <= end_date,
            Resume.job_category.in_(agent_job_names),
            Resume.file_type.in_(['pdf', 'docx']),
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).group_by(date_format).order_by(date_format).all()

        return {
            r.date: {
                "total": r.total,
                "pass": int(getattr(r, 'pass')) if getattr(r, 'pass') else 0,
                "review": int(r.review) if r.review else 0,
                "reject": int(r.reject) if r.reject else 0,
                "avg_score": round(float(r.avg_score), 2) if r.avg_score else 0
            }
            for r in results
        }
    except Exception as e:
        logger.error(f"获取时间段统计失败: {str(e)}")
        return {}
    finally:
        db.close()
