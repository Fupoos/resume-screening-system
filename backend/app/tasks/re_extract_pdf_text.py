"""重新提取无文本PDF的内容并分类

使用pdfplumber重新解析PDF文件
"""

import sys
import os

sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.school_classifier import get_school_classifier
from app.tasks.re_extract_education import extract_education_from_text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def re_extract_pdf_text():
    """重新提取PDF文本"""
    db = SessionLocal()

    try:
        # 查询无文本的PDF简历
        resumes = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.education_level.is_(None),
            (Resume.raw_text.is_(None) | (Resume.raw_text == ''))
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份无文本的PDF简历需要重新提取")

        classifier = get_school_classifier()
        success_count = 0
        failed_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                file_path = resume.file_path
                if not file_path or not os.path.exists(file_path):
                    logger.debug(f"简历 {idx}/{total} 文件不存在: {file_path}")
                    failed_count += 1
                    continue

                # 使用pdfplumber提取文本
                import pdfplumber
                text = ""
                try:
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"pdfplumber解析失败 {file_path}: {str(e)}")
                    # 尝试PyMuPDF
                    try:
                        import fitz
                        doc = fitz.open(file_path)
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        doc.close()
                    except Exception as e2:
                        logger.warning(f"PyMuPDF也失败: {str(e2)}")
                        failed_count += 1
                        continue

                if not text or len(text.strip()) < 100:
                    logger.debug(f"简历 {idx}/{total} 提取文本过短或为空")
                    failed_count += 1
                    continue

                # 清理文本：去除NUL字符和其他控制字符
                text = text.replace('\x00', '').strip()
                # 限制文本长度（避免过长）
                if len(text) > 50000:
                    text = text[:50000]

                # 更新raw_text
                resume.raw_text = text

                # 提取教育信息
                education_history = extract_education_from_text(text)

                if education_history:
                    resume.education_history = education_history

                    # 判断最高学历的学校类型
                    highest_edu = education_history[0]
                    school_name = highest_edu.get('school', '')

                    if school_name:
                        school_type = classifier.classify(school_name)
                        resume.education_level = school_type

                        db.commit()
                        success_count += 1

                        if idx % 20 == 0 or idx == total:
                            logger.info(
                                f"进度: {idx}/{total} | "
                                f"成功: {success_count} | "
                                f"失败: {failed_count} | "
                                f"学校: {school_name[:30]} -> {school_type}"
                            )
                else:
                    # 即使没找到教育信息，也保存提取的文本
                    db.commit()
                    logger.debug(f"简历 {idx}/{total} 未找到教育信息")
                    failed_count += 1

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                failed_count += 1
                continue

        logger.info("=" * 60)
        logger.info("PDF文本重新提取完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"成功提取并分类: {success_count}")
        logger.info(f"失败: {failed_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"批量更新失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    re_extract_pdf_text()
