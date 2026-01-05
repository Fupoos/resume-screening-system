"""批量更新学历等级字段（education_level）

使用内置大学分类服务，从简历文本中提取学校并分类为985/211/QS前50/100/200/双非

使用方法：
    docker-compose exec backend python3 -m app.tasks.update_education_level
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.university_classifier import classify_education_level
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_education_level():
    """批量更新学历等级字段"""
    db = SessionLocal()

    try:
        # 查询所有有原始文本的简历
        resumes = db.query(Resume).filter(
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份有原始文本的简历\n")

        updated_count = 0
        no_level_count = 0
        already_has_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                # 跳过已有education_level的简历
                if resume.education_level:
                    already_has_count += 1
                    if idx % 100 == 0 or idx == total:
                        logger.info(
                            f"进度: {idx}/{total} | "
                            f"已有等级: {already_has_count} | "
                            f"已更新: {updated_count} | "
                            f"未找到: {no_level_count}"
                        )
                    continue

                # 从原始文本分类学历等级
                level = classify_education_level(resume.raw_text)

                if level:
                    resume.education_level = level
                    db.commit()
                    updated_count += 1

                    if idx % 100 == 0 or idx == total:
                        logger.info(
                            f"进度: {idx}/{total} | "
                            f"已有等级: {already_has_count} | "
                            f"已更新: {updated_count} | "
                            f"未找到: {no_level_count} | "
                            f"最新: {resume.candidate_name or '未命名'} -> {resume.education or '?'} / {level}"
                        )
                else:
                    no_level_count += 1

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                continue

        logger.info("\n" + "=" * 80)
        logger.info("学历等级更新完成！")
        logger.info("=" * 80)
        logger.info(f"总简历数: {total}")
        logger.info(f"已有等级: {already_has_count}")
        logger.info(f"成功更新: {updated_count}")
        logger.info(f"未找到等级: {no_level_count}")
        logger.info("=" * 80)

        # 统计各等级数量
        logger.info("\n学历等级分布:")
        resumes = db.query(Resume).filter(
            Resume.education_level.isnot(None)
        ).all()

        level_count = {}
        for resume in resumes:
            level = resume.education_level
            if level not in level_count:
                level_count[level] = 0
            level_count[level] += 1

        for level, count in sorted(level_count.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {level}: {count}")

    except Exception as e:
        logger.error(f"批量更新失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始批量更新学历等级...\n")
    update_education_level()
