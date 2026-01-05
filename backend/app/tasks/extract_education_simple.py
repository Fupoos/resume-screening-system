"""简化版：重新提取学历字段（education）

只提取education字段（学历文本：本科/硕士/博士等）
不做学校分类（education_level需要由Agent完成）

使用方法：
    docker-compose exec backend python3 -m app.tasks.extract_education_simple
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_degree_from_text(text: str) -> str:
    """从原始文本中提取最高学历

    按优先级查找：博士 > 硕士 > 本科 > 大专 > 其他
    """
    if not text:
        return None

    # 只检查前5000字符（教育背景通常在前半部分）
    text = text[:5000]

    # 学历关键词（按优先级排序）
    degrees = [
        '博士研究生', '博士',
        '硕士研究生', '硕士',
        '研究生',
        '本科', '学士',
        '大专', '专科',
        '高中', '中专'
    ]

    # 查找最高学历
    for degree in degrees:
        if degree in text:
            return degree

    return None


def extract_education_simple():
    """简化版：只提取education字段"""
    db = SessionLocal()

    try:
        # 查询所有有原始文本的简历
        resumes = db.query(Resume).filter(
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份有原始文本的简历")

        updated_count = 0
        no_edu_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                # 跳过已有education的简历
                if resume.education:
                    logger.debug(f"简历 {idx}/{total} 已有education，跳过")
                    continue

                # 从原始文本提取学历
                degree = extract_degree_from_text(resume.raw_text)

                if degree:
                    resume.education = degree
                    db.commit()
                    updated_count += 1

                    if idx % 100 == 0 or idx == total:
                        logger.info(
                            f"进度: {idx}/{total} | "
                            f"已更新: {updated_count} | "
                            f"无学历: {no_edu_count} | "
                            f"最新: {resume.candidate_name or '未命名'} -> {degree}"
                        )
                else:
                    no_edu_count += 1

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                continue

        logger.info("=" * 60)
        logger.info("学历提取完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"成功更新: {updated_count}")
        logger.info(f"未找到学历: {no_edu_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"批量更新失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    extract_education_simple()
