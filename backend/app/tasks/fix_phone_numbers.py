"""重新提取和清理电话号码

对于所有PDF简历，重新提取电话号码并清理格式
"""

import sys
import os
import re

sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_phone_number(phone: str) -> str:
    """清理电话号码格式

    去除括号、横杠、空格、+86等，只保留11位手机号
    """
    if not phone:
        return phone

    # 去除所有非数字字符
    cleaned = re.sub(r'[^\d]', '', phone)

    # 如果是12位且以86开头，去掉86
    if len(cleaned) == 12 and cleaned.startswith('86'):
        cleaned = cleaned[2:]

    # 中国手机号是11位且以1开头
    if len(cleaned) == 11 and cleaned.startswith('1'):
        return cleaned

    # 如果不符合，返回原始值
    return phone


def fix_phone_numbers():
    """重新提取和清理电话号码"""
    db = SessionLocal()

    try:
        # 查询所有PDF简历
        resumes = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None)
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份PDF简历需要检查电话号码")

        parser = ResumeParser()
        fixed_count = 0
        cleaned_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                original_phone = resume.phone

                # 重新从原始文本提取电话
                if resume.raw_text:
                    new_phone = parser._extract_phone(resume.raw_text)

                    if new_phone:
                        # 清理格式
                        cleaned_phone = clean_phone_number(new_phone)

                        if cleaned_phone != original_phone:
                            resume.phone = cleaned_phone
                            db.commit()

                            if original_phone:
                                fixed_count += 1
                            else:
                                fixed_count += 1

                            if idx % 50 == 0 or idx == total:
                                logger.info(
                                    f"进度: {idx}/{total} | "
                                    f"修复: {fixed_count} | "
                                    f"原始: {original_phone} -> {cleaned_phone}"
                                )

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                continue

        logger.info("=" * 60)
        logger.info("电话号码修复完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"成功修复: {fixed_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"修复失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    fix_phone_numbers()
