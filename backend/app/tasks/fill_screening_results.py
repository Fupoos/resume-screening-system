"""填充screening_results表 - 为有真实Agent评分的简历创建记录

为符合CLAUDE.md原则2且有真实FastGPT评分的简历创建screening_results记录。

根据CLAUDE.md核心原则：
- 所有简历打分必须通过外部Agent完成
- 只保留有PDF+正文的简历
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.models.screening_result import ScreeningResult
from sqlalchemy import and_
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 预设岗位列表（与app/data/jobs.py保持一致）
PRESET_JOBS = [
    {
        'id': '550e8400-e29b-41d4-a716-446655440001',
        'name': '实施顾问',
        'department': '实施部',
        'description': '负责公司产品的实施和客户培训',
        'requirements': ['3年以上实施经验', '良好的沟通能力', '能适应出差'],
        'city': '上海',
        'salary_min': 15000,
        'salary_max': 25000,
        'status': 'active'
    },
    {
        'id': '550e8400-e29b-41d4-a716-446655440002',
        'name': 'Java开发',
        'department': '研发部',
        'description': '负责后端系统开发',
        'requirements': ['3年以上Java开发经验', '熟悉Spring框架'],
        'city': '上海',
        'salary_min': 20000,
        'salary_max': 35000,
        'status': 'active'
    },
    {
        'id': '550e8400-e29b-41d4-a716-446655440003',
        'name': '前端开发',
        'department': '研发部',
        'description': '负责前端页面开发',
        'requirements': ['2年以上前端经验', '熟悉React或Vue'],
        'city': '上海',
        'salary_min': 15000,
        'salary_max': 28000,
        'status': 'active'
    }
]


def fill_screening_results():
    """为有真实Agent评分的简历创建screening_results记录"""
    db = SessionLocal()

    try:
        # 1. 找到实施顾问岗位ID
        implementation_job = None
        for job in PRESET_JOBS:
            if job.get('name') == '实施顾问':
                implementation_job = job
                break

        if not implementation_job:
            logger.error("❌ 未找到「实施顾问」岗位")
            return

        job_id = implementation_job['id']
        logger.info(f"找到岗位: {implementation_job['name']} (ID: {job_id})")

        # 2. 查找有真实评分的实施顾问简历
        # 条件：
        # - job_category = '实施顾问'
        # - agent_score IS NOT NULL
        # - agent_score != 50 (排除默认值)
        # - file_type = 'pdf'
        # - raw_text IS NOT NULL (符合CLAUDE.md原则2)
        evaluated_resumes = db.query(Resume).filter(
            and_(
                Resume.job_category == '实施顾问',
                Resume.agent_score.isnot(None),
                Resume.agent_score != 50,
                Resume.file_type == 'pdf',
                Resume.raw_text.isnot(None),
                Resume.raw_text != ''
            )
        ).all()

        if not evaluated_resumes:
            logger.info("✅ 没有需要填充的简历")
            return

        logger.info(f"\n找到 {len(evaluated_resumes)} 份有真实评分的实施顾问简历")

        # 统计评分分布
        score_distribution = {
            'PASS': 0,      # >= 70分
            'REVIEW': 0,    # >= 40分
            'REJECT': 0     # < 40分
        }

        # 3. 为每份简历创建screening_result记录
        created_count = 0
        skipped_count = 0

        logger.info("\n开始创建screening_results记录...")

        for idx, resume in enumerate(evaluated_resumes, 1):
            # 检查是否已存在
            existing = db.query(ScreeningResult).filter(
                ScreeningResult.resume_id == resume.id
            ).first()

            if existing:
                skipped_count += 1
                logger.info(
                    f"[{idx}/{len(evaluated_resumes)}] 跳过: {resume.candidate_name} "
                    f"(评分: {resume.agent_score}) - 已存在screening_result"
                )
                continue

            # 根据评分确定筛选结果
            score = resume.agent_score
            if score >= 70:
                screening_result = 'PASS'
                score_distribution['PASS'] += 1
                result_text = 'PASS (可以发offer)'
            elif score >= 40:
                screening_result = 'REVIEW'
                score_distribution['REVIEW'] += 1
                result_text = 'REVIEW (待定)'
            else:
                screening_result = 'REJECT'
                score_distribution['REJECT'] += 1
                result_text = 'REJECT (不合格)'

            # 创建screening_result记录
            screening = ScreeningResult(
                resume_id=resume.id,
                job_id=job_id,
                match_score=score,
                screening_result=screening_result,
                suggestion=f"Agent评分: {score}分"
            )
            db.add(screening)
            created_count += 1

            logger.info(
                f"[{idx}/{len(evaluated_resumes)}] 创建: {resume.candidate_name} "
                f"- 评分: {score}分 → {result_text}"
            )

        # 提交更改
        db.commit()

        logger.info("\n" + "=" * 80)
        logger.info(f"✅ 成功创建 {created_count} 条screening_results记录")
        logger.info(f"   跳过 {skipped_count} 条已存在记录")
        logger.info("=" * 80)

        # 显示评分分布
        logger.info("\n评分分布:")
        logger.info("-" * 80)
        logger.info(f"  PASS (>=70分):     {score_distribution['PASS']} 份")
        logger.info(f"  REVIEW (40-69分):  {score_distribution['REVIEW']} 份")
        logger.info(f"  REJECT (<40分):    {score_distribution['REJECT']} 份")
        logger.info("-" * 80)

        # 验证结果
        total_screenings = db.query(ScreeningResult).filter(
            ScreeningResult.job_id == job_id
        ).count()

        logger.info(f"\nscreening_results表验证:")
        logger.info(f"  实施顾问岗位的总筛选记录数: {total_screenings}")

        # 显示最高分的10份简历
        logger.info("\n最高分的10份简历:")
        logger.info("-" * 80)
        top_resumes = db.query(ScreeningResult, Resume).join(
            Resume, ScreeningResult.resume_id == Resume.id
        ).filter(
            ScreeningResult.job_id == job_id
        ).order_by(
            ScreeningResult.match_score.desc()
        ).limit(10).all()

        for idx, (screening, resume) in enumerate(top_resumes, 1):
            logger.info(
                f"  {idx}. {resume.candidate_name} - "
                f"评分: {screening.match_score}分, "
                f"结果: {screening.screening_result}"
            )
        logger.info("-" * 80)

    except Exception as e:
        logger.error(f"填充失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始填充screening_results表...\n")
    fill_screening_results()
