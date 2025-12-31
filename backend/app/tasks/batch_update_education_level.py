"""批量更新现有简历的 education_level 字段

这个脚本会重新判断所有历史简历的学校类型
"""

import sys
import os

# 设置Python路径
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.school_classifier import get_school_classifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def batch_update_education_level():
    """批量更新所有简历的 education_level"""
    db = SessionLocal()

    try:
        # 查询所有简历
        resumes = db.query(Resume).all()
        total = len(resumes)
        logger.info(f"找到 {total} 份简历需要更新")

        classifier = get_school_classifier()

        updated_count = 0
        not_found_count = 0
        no_education_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                # 只更新没有 education_level 的简历
                if resume.education_level is not None:
                    logger.debug(f"简历 {idx}/{total} 已有 education_level，跳过")
                    continue

                # 从 education_history 中获取最高学历的学校
                education_history = resume.education_history
                if not education_history or len(education_history) == 0:
                    logger.debug(f"简历 {idx}/{total} 没有教育背景，跳过")
                    no_education_count += 1
                    continue

                # 取第一个（最高学历）
                highest_edu = education_history[0]
                school_name = highest_edu.get('school', '')

                if not school_name:
                    logger.debug(f"简历 {idx}/{total} 没有学校名称，跳过")
                    not_found_count += 1
                    continue

                # 判断学校类型
                school_type = classifier.classify(school_name)

                if school_type:
                    # 更新数据库
                    resume.education_level = school_type
                    db.commit()
                    updated_count += 1

                    if idx % 100 == 0 or idx == total:
                        logger.info(
                            f"进度: {idx}/{total} | "
                            f"已更新: {updated_count} | "
                            f"学校: {school_name} -> {school_type}"
                        )
                else:
                    not_found_count += 1

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                continue

        logger.info("=" * 60)
        logger.info("批量更新完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"成功更新: {updated_count}")
        logger.info(f"未找到学校: {not_found_count}")
        logger.info(f"无教育背景: {no_education_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"批量更新失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    batch_update_education_level()
