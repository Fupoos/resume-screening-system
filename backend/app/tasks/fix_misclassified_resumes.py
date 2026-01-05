"""修正被错误分类的简历

使用方法：
    docker-compose exec backend python3 -m app.tasks.fix_misclassified_resumes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import logging
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.job_title_classifier import JobTitleClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_misclassified_resumes():
    """重新分类所有简历，使用改进后的JobTitleClassifier"""
    db = SessionLocal()

    try:
        # 查找所有有PDF且有正文的简历
        resumes = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).all()

        logger.info(f"总简历数: {len(resumes)}")

        classifier = JobTitleClassifier()

        fixed_count = 0
        unchanged_count = 0
        error_count = 0

        for resume in resumes:
            try:
                # 重新分类
                new_category = classifier.classify_job_title(
                    email_subject=resume.source_email_subject or "",
                    resume_text=resume.raw_text or "",
                )

                # 检查是否需要更新
                old_category = resume.job_category or "待分类"

                if old_category != new_category:
                    logger.info(
                        f"修正: {resume.candidate_name} | "
                        f"{old_category} → {new_category} | "
                        f"邮件: {resume.source_email_subject or '无'}"
                    )
                    resume.job_category = new_category
                    fixed_count += 1
                else:
                    unchanged_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"处理简历 {resume.id} 失败: {e}")

        # 提交所有更改
        db.commit()

        logger.info("\n" + "=" * 80)
        logger.info("修复完成！")
        logger.info(f"  总简历数: {len(resumes)}")
        logger.info(f"  修正数量: {fixed_count}")
        logger.info(f"  未变动: {unchanged_count}")
        logger.info(f"  错误数量: {error_count}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"修复失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始修正被错误分类的简历...\n")
    fix_misclassified_resumes()
