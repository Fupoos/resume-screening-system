"""清理岗位数据库，只保留7个岗位类别

使用方法：
    docker-compose exec backend python3 -m app.tasks.cleanup_jobs
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.job import Job
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 用户定义的7个岗位类别
VALID_JOB_NAMES = [
    "Java开发",
    "销售总监",
    "自动化测试",
    "市场运营",
    "前端开发",
    "产品经理",
    "实施顾问",
]


def cleanup_jobs():
    """清理岗位数据库，只保留7个岗位类别"""
    db = SessionLocal()

    try:
        # 1. 查看当前所有岗位
        all_jobs = db.query(Job).all()
        total_count = len(all_jobs)

        logger.info(f"当前数据库中共有 {total_count} 个岗位\n")

        # 2. 分类：需要保留的 vs 需要删除的
        jobs_to_keep = []
        jobs_to_delete = []

        for job in all_jobs:
            if job.name in VALID_JOB_NAMES:
                jobs_to_keep.append(job)
            else:
                jobs_to_delete.append(job)

        logger.info(f"需要保留的岗位: {len(jobs_to_keep)} 个")
        for job in jobs_to_keep:
            logger.info(f"  ✓ {job.name} (category={job.category}, agent={job.agent_type})")

        logger.info(f"\n需要删除的岗位: {len(jobs_to_delete)} 个")
        for job in jobs_to_delete:
            logger.info(f"  ✗ {job.name} (category={job.category}, agent={job.agent_type})")

        # 3. 删除不属于7个类别的岗位
        if jobs_to_delete:
            logger.info(f"\n开始删除 {len(jobs_to_delete)} 个无效岗位...")

            deleted_count = 0
            for job in jobs_to_delete:
                try:
                    # 删除关联的screening_results
                    from app.models.screening_result import ScreeningResult
                    screenings = db.query(ScreeningResult).filter(
                        ScreeningResult.job_id == job.id
                    ).all()

                    for screening in screenings:
                        db.delete(screening)

                    # 删除岗位
                    db.delete(job)
                    db.commit()
                    deleted_count += 1
                    logger.info(f"  ✅ 已删除: {job.name}")

                except Exception as e:
                    logger.error(f"  ❌ 删除失败 {job.name}: {e}")
                    db.rollback()

            logger.info(f"\n成功删除 {deleted_count} 个岗位")
        else:
            logger.info("\n没有需要删除的岗位")

        # 4. 确认7个岗位都存在
        logger.info("\n" + "=" * 80)
        logger.info("验证7个岗位是否都存在:")
        logger.info("=" * 80)

        final_jobs = db.query(Job).all()
        final_job_names = [job.name for job in final_jobs]

        for valid_name in VALID_JOB_NAMES:
            if valid_name in final_job_names:
                job = db.query(Job).filter(Job.name == valid_name).first()
                logger.info(f"  ✅ {valid_name}: 存在 (ID={job.id}, agent={job.agent_type})")
            else:
                logger.warning(f"  ❌ {valid_name}: 不存在！需要创建")

        logger.info("\n" + "=" * 80)
        logger.info(f"清理完成！剩余岗位数: {len(final_jobs)}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"清理失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始清理岗位数据库...\n")
    cleanup_jobs()
