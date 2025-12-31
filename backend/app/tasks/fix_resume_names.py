"""修复错误识别的名字和电话号码格式

对于candidate_name字段值错误（如"出生年月"、"求职信息"）的简历，重新提取名字
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

    去除横杠、空格等分隔符
    """
    if not phone:
        return phone

    # 去除所有非数字字符
    cleaned = re.sub(r'[^\d]', '', phone)

    # 中国手机号是11位
    if len(cleaned) == 11 and cleaned.startswith('1'):
        return cleaned

    # 如果不是11位或不是1开头，返回原始值
    return phone


def fix_resume_names():
    """修复错误识别的名字"""
    db = SessionLocal()

    try:
        # 查询名字识别错误的简历
        from sqlalchemy import or_

        # 构建查询条件
        bad_names = [
            '出生年月', '求职信息', '求职意向', '教育背景', '基本信息',
            '联系方式', '个人简历', '个人信息', '个人总结', '个人简介',
            '个人评价', '教育经历', '工作经历', '项目经验', '自我评价',
            '优势亮点', '掌握技能', '资格证书', '双一流',
            '会计', '会计学', '审计', '统计学',
            '本科学位', '硕士学位', '博士学位',
            '上海', '北京', '深圳', '广州', '长春',
            '明源云', '用友', '金蝶', '卫泰集团', '唯泰集团', '核心技能'
        ]

        resumes = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            or_(
                Resume.candidate_name.in_(bad_names),
                Resume.candidate_name.like('%教育%'),
                Resume.candidate_name.like('%求职%'),
                Resume.candidate_name.like('%出生%'),
                Resume.candidate_name.like('%个人%'),
                Resume.candidate_name.like('%基本%'),
                Resume.candidate_name.like('%联系%'),
                Resume.candidate_name == '',
                Resume.candidate_name == None
            )
        ).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份需要修复名字的简历")

        parser = ResumeParser()
        fixed_count = 0
        phone_fixed_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                new_name = None

                # 1. 从原始文本提取名字
                if resume.raw_text:
                    new_name = parser._extract_name(resume.raw_text)

                # 2. 如果文本提取失败，尝试从文件名提取
                if not new_name and resume.file_path:
                    new_name = parser._extract_name_from_filename(resume.file_path)

                # 如果找到了新名字且与旧名字不同，更新
                if new_name and new_name != resume.candidate_name:
                    resume.candidate_name = new_name
                    fixed_count += 1

                # 清理电话号码格式
                if resume.phone:
                    cleaned_phone = clean_phone_number(resume.phone)
                    if cleaned_phone != resume.phone:
                        resume.phone = cleaned_phone
                        phone_fixed_count += 1

                db.commit()

                if idx % 50 == 0 or idx == total:
                    logger.info(
                        f"进度: {idx}/{total} | "
                        f"名字修复: {fixed_count} | "
                        f"电话修复: {phone_fixed_count} | "
                        f"当前: {resume.candidate_name}"
                    )

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                continue

        logger.info("=" * 60)
        logger.info("修复完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"名字修复: {fixed_count}")
        logger.info(f"电话格式修复: {phone_fixed_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"修复失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    fix_resume_names()
