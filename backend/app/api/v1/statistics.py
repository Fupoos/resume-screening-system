"""统计API - 提供简历筛选的统计分析功能"""
from fastapi import APIRouter, Query
from sqlalchemy import func, case
from app.core.database import SessionLocal
from app.models.resume import Resume
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_statistics():
    """获取Dashboard综合统计数据

    Returns:
        {
            "overview": {
                "total_resumes": int,      # 总简历数
                "pass_count": int,          # 可以发offer数量
                "review_count": int,        # 待定数量
                "reject_count": int,        # 不合格数量
                "pass_rate": float,         # 通过率
                "avg_score": float          # 平均分
            }
        }
    """
    db = SessionLocal()
    try:
        # 总体统计
        total = db.query(func.count(Resume.id)).scalar()

        pass_count = db.query(func.count(Resume.id)).filter(
            Resume.screening_status == '可以发offer'
        ).scalar()

        review_count = db.query(func.count(Resume.id)).filter(
            Resume.screening_status == '待定'
        ).scalar()

        reject_count = db.query(func.count(Resume.id)).filter(
            Resume.screening_status == '不合格'
        ).scalar()

        avg_score = db.query(func.avg(Resume.agent_score)).scalar()

        return {
            "overview": {
                "total_resumes": total or 0,
                "pass_count": pass_count or 0,
                "review_count": review_count or 0,
                "reject_count": reject_count or 0,
                "pass_rate": round((pass_count / total), 3) if total and total > 0 else 0,
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
async def get_statistics_by_city():
    """按城市统计

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
        results = db.query(
            Resume.city,
            func.count(Resume.id).label('total'),
            func.sum(case((Resume.screening_status == '可以发offer', 1), else_=0)).label('pass'),
            func.sum(case((Resume.screening_status == '待定', 1), else_=0)).label('review'),
            func.sum(case((Resume.screening_status == '不合格', 1), else_=0)).label('reject'),
            func.avg(Resume.agent_score).label('avg_score')
        ).group_by(Resume.city).all()

        return {
            (r.city or "未知"): {
                "total": r.total,
                "pass": int(r.pass) if r.pass else 0,
                "review": int(r.review) if r.review else 0,
                "reject": int(r.reject) if r.reject else 0,
                "avg_score": round(float(r.avg_score), 2) if r.avg_score else 0,
                "pass_rate": round((int(r.pass) / r.total), 3) if r.total and r.total > 0 else 0
            }
            for r in results
        }
    except Exception as e:
        logger.error(f"获取城市统计失败: {str(e)}")
        return {}
    finally:
        db.close()


@router.get("/by-job")
async def get_statistics_by_job():
    """按具体职位统计

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
        results = db.query(
            Resume.job_category,
            func.count(Resume.id).label('total'),
            func.sum(case((Resume.screening_status == '可以发offer', 1), else_=0)).label('pass'),
            func.sum(case((Resume.screening_status == '待定', 1), else_=0)).label('review'),
            func.sum(case((Resume.screening_status == '不合格', 1), else_=0)).label('reject'),
            func.avg(Resume.agent_score).label('avg_score')
        ).group_by(Resume.job_category).all()

        return {
            (r.job_category or "待分类"): {
                "total": r.total,
                "pass": int(r.pass) if r.pass else 0,
                "review": int(r.review) if r.review else 0,
                "reject": int(r.reject) if r.reject else 0,
                "avg_score": round(float(r.avg_score), 2) if r.avg_score else 0
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
    group_by: str = Query("day", description="分组方式: day/week/month")
):
    """按时间段统计

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

        # 查询统计数据
        results = db.query(
            date_label.label('date'),
            func.count(Resume.id).label('total'),
            func.sum(case((Resume.screening_status == '可以发offer', 1), else_=0)).label('pass'),
            func.sum(case((Resume.screening_status == '待定', 1), else_=0)).label('review'),
            func.sum(case((Resume.screening_status == '不合格', 1), else_=0)).label('reject'),
            func.avg(Resume.agent_score).label('avg_score')
        ).filter(
            Resume.created_at >= start_date,
            Resume.created_at <= end_date
        ).group_by(date_format).order_by(date_format).all()

        return {
            r.date: {
                "total": r.total,
                "pass": int(r.pass) if r.pass else 0,
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
