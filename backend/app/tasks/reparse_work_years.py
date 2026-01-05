"""重新计算工作年限（排除在校期间的实习和课程）

使用方法：
    docker-compose exec backend python3 -m app.tasks.reparse_work_years
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reparse_work_years():
    """重新计算所有简历的工作年限"""
    db = SessionLocal()

    try:
        # 查询所有有原始文本的简历
        resumes = db.query(Resume).filter(
            Resume.raw_text.isnot(None),
            Resume.raw_text != '',
            Resume.file_path.isnot(None),
            Resume.file_path != ''
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份有PDF和正文的简历\n")

        updated_count = 0
        no_change_count = 0
        error_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                # 重新解析工作经历
                parser = ResumeParser()

                # 只重新解析工作经历部分
                work_experience = parser._extract_work_experience(resume.raw_text)
                new_work_years = parser._calculate_work_years(work_experience)

                # 获取旧的工作年限
                old_work_years = resume.work_years

                # 检查是否有变化
                if old_work_years != new_work_years:
                    # 更新数据库
                    resume.work_years = new_work_years
                    resume.work_experience = work_experience
                    db.commit()
                    updated_count += 1

                    if idx % 50 == 0 or idx == total:
                        logger.info(
                            f"进度: {idx}/{total} | "
                            f"已更新: {updated_count} | "
                            f"无变化: {no_change_count} | "
                            f"错误: {error_count} | "
                            f"最新: {resume.candidate_name or '未命名'} {old_work_years}年→{new_work_years}年"
                        )
                else:
                    no_change_count += 1

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                error_count += 1
                continue

        logger.info("\n" + "=" * 80)
        logger.info("工作年限重新计算完成！")
        logger.info("=" * 80)
        logger.info(f"总简历数: {total}")
        logger.info(f"成功更新: {updated_count}")
        logger.info(f"无变化: {no_change_count}")
        logger.info(f"错误: {error_count}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"批量更新失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始重新计算工作年限...\n")
    reparse_work_years()
