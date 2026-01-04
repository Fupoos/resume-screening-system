"""数据清理脚本 - 清理无效的Agent评分

清理非实施顾问职位的无效50分默认评分。

根据CLAUDE.md核心原则：
- 所有简历打分必须通过外部Agent完成
- 禁止使用默认评分或本地评分
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from sqlalchemy import and_
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_invalid_scores():
    """清理无效的Agent评分（非实施顾问职位的50分默认值）"""
    db = SessionLocal()

    try:
        # 查找需要清理的简历：
        # - job_category != '实施顾问'
        # - agent_score = 50 (默认值)
        invalid_resumes = db.query(Resume).filter(
            and_(
                Resume.job_category != '实施顾问',
                Resume.agent_score == 50
            )
        ).all()

        if not invalid_resumes:
            logger.info("✅ 没有需要清理的无效评分")
            return

        logger.info(f"找到 {len(invalid_resumes)} 份需要清理的简历")
        logger.info("\n开始清理...")

        # 清理每份简历的评分
        for idx, resume in enumerate(invalid_resumes, 1):
            logger.info(
                f"[{idx}/{len(invalid_resumes)}] 清理: {resume.candidate_name} "
                f"({resume.job_category}) - 旧评分: {resume.agent_score}"
            )

            # 清除评分相关字段
            resume.agent_score = None
            resume.agent_evaluation_id = None
            resume.agent_evaluated_at = None
            resume.screening_status = 'pending'

        # 提交更改
        db.commit()

        logger.info("\n" + "=" * 80)
        logger.info(f"✅ 成功清理 {len(invalid_resumes)} 条无效评分记录")
        logger.info("=" * 80)

        # 验证清理结果
        logger.info("\n验证清理结果...")

        # 检查是否还有非实施顾问的50分记录
        remaining_invalid = db.query(Resume).filter(
            and_(
                Resume.job_category != '实施顾问',
                Resume.agent_score == 50
            )
        ).count()

        # 统计各职位评分情况
        score_stats = db.query(
            Resume.job_category,
            db.func.count(Resume.id).label('count'),
            db.func.avg(Resume.agent_score).label('avg_score')
        ).filter(
            Resume.agent_score.isnot(None)
        ).group_by(Resume.job_category).all()

        logger.info(f"\n剩余无效50分记录: {remaining_invalid}")
        logger.info("\n当前各职位评分统计:")
        logger.info("-" * 80)
        for stat in score_stats:
            logger.info(
                f"  {stat.job_category or '待分类'}: "
                f"{stat.count} 份简历, "
                f"平均分: {stat.avg_score:.2f}"
            )
        logger.info("-" * 80)

    except Exception as e:
        logger.error(f"清理失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始清理无效的Agent评分...\n")
    cleanup_invalid_scores()
