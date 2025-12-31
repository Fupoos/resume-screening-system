"""重新分类所有简历的学历等级

即使已有education_history，也重新判断education_level
"""

import sys
import os

sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.school_classifier import get_school_classifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reclassify_all_education():
    """重新分类所有简历的学历等级"""
    db = SessionLocal()

    try:
        # 查询所有有education_history的简历
        resumes = db.query(Resume).filter(
            Resume.education_history.isnot(None),
            Resume.education_history != '[]'
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份有教育历史的简历需要重新分类")

        classifier = get_school_classifier()

        updated_count = 0
        not_found_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                education_history = resume.education_history
                if not education_history or len(education_history) == 0:
                    not_found_count += 1
                    continue

                # 取第一个（最高学历）
                highest_edu = education_history[0]
                school_name = highest_edu.get('school', '')

                if not school_name:
                    not_found_count += 1
                    continue

                # 判断学校类型
                old_level = resume.education_level
                school_type = classifier.classify(school_name)

                if school_type != old_level:
                    # 更新数据库
                    resume.education_level = school_type
                    db.commit()
                    updated_count += 1

                    if idx % 50 == 0 or idx == total:
                        logger.info(
                            f"进度: {idx}/{total} | "
                            f"已更新: {updated_count} | "
                            f"学校: {school_name} | {old_level} -> {school_type}"
                        )
                else:
                    if idx % 50 == 0 or idx == total:
                        logger.debug(f"简历 {idx}/{total} 无需更新: {school_name} -> {school_type}")

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                continue

        logger.info("=" * 60)
        logger.info("重新分类完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"成功更新: {updated_count}")
        logger.info(f"无学校: {not_found_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"重新分类失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    reclassify_all_education()
