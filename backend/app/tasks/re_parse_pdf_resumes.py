"""重新解析PDF简历，提取所有信息

对于有raw_text但缺少基本信息的简历，重新解析
"""

import sys
import os

sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def re_parse_pdf_resumes():
    """重新解析PDF简历"""
    db = SessionLocal()

    try:
        # 查询有raw_text但没有姓名的PDF简历
        resumes = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != '',
            (Resume.candidate_name.is_(None) | (Resume.candidate_name == ''))
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份需要重新解析的PDF简历")

        parser = ResumeParser()
        success_count = 0
        failed_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                # 使用完整的简历解析器
                parsed_data = parser.parse_resume(resume.file_path)

                # 更新所有字段
                if parsed_data.get('candidate_name'):
                    resume.candidate_name = parsed_data.get('candidate_name')
                if parsed_data.get('phone'):
                    resume.phone = parsed_data.get('phone')
                if parsed_data.get('email'):
                    resume.email = parsed_data.get('email')
                if parsed_data.get('education'):
                    resume.education = parsed_data.get('education')
                if parsed_data.get('work_years'):
                    resume.work_years = parsed_data.get('work_years', 0)
                if parsed_data.get('skills'):
                    resume.skills = parsed_data.get('skills', [])
                if parsed_data.get('work_experience'):
                    resume.work_experience = parsed_data.get('work_experience', [])
                if parsed_data.get('project_experience'):
                    resume.project_experience = parsed_data.get('project_experience', [])
                if parsed_data.get('education_history'):
                    resume.education_history = parsed_data.get('education_history', [])

                # 保存
                db.commit()
                success_count += 1

                if idx % 20 == 0 or idx == total:
                    logger.info(
                        f"进度: {idx}/{total} | "
                        f"成功: {success_count} | "
                        f"姓名: {resume.candidate_name}"
                    )

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                failed_count += 1
                continue

        logger.info("=" * 60)
        logger.info("PDF简历重新解析完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"成功解析: {success_count}")
        logger.info(f"失败: {failed_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"批量解析失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    re_parse_pdf_resumes()
