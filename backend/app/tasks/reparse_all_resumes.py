"""全面重新解析所有简历（使用最新解析逻辑）

更新字段：
- candidate_name: 候选人姓名
- phone: 电话
- email: 邮箱
- education: 最高学历
- education_level: 学历等级（985/211/双非等）
- work_years: 工作年限
- skills: 技能列表
- skills_by_level: 按熟练度分类的技能
- work_experience: 工作经历
- project_experience: 项目经历
- education_history: 教育背景

使用方法：
    docker-compose exec backend python3 -m app.tasks.reparse_all_resumes
"""
import sys
import os
import logging

# 必须在所有其他导入之前配置日志
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
from app.utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


def reparse_all_resumes(limit: int = 200):
    """使用最新解析逻辑重新解析所有简历

    Args:
        limit: 重新解析的简历数量，默认200份（最近的）
    """
    db = SessionLocal()

    try:
        # 查询最近N份有原始文本的简历（按创建时间倒序）
        resumes = db.query(Resume).filter(
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).order_by(Resume.created_at.desc()).limit(limit).all()

        total = len(resumes)
        logger.info(f"找到 {total} 份有正文的简历\n")

        updated_count = 0
        no_change_count = 0
        error_count = 0

        parser = ResumeParser()

        for idx, resume in enumerate(resumes, 1):
            try:
                # 先清理文本（处理单字行等问题）
                cleaned_text = TextCleaner.clean_text(resume.raw_text)

                # 使用最新的解析逻辑重新解析
                parsed_data = parser._parse_text(
                    cleaned_text,
                    email_subject=resume.source_email_subject,
                    filename=resume.file_path
                )

                # 检查是否有变化
                has_change = False
                changes = []

                # 比较各个字段
                old_name = resume.candidate_name
                new_name = parsed_data.get('candidate_name')
                if old_name != new_name:
                    has_change = True
                    changes.append(f"姓名: {old_name} -> {new_name}")
                    resume.candidate_name = new_name

                old_phone = resume.phone
                new_phone = parsed_data.get('phone')
                if old_phone != new_phone:
                    has_change = True
                    changes.append(f"电话: {old_phone} -> {new_phone}")
                    resume.phone = new_phone

                old_email = resume.email
                new_email = parsed_data.get('email')
                if old_email != new_email:
                    has_change = True
                    changes.append(f"邮箱: {old_email} -> {new_email}")
                    resume.email = new_email

                old_edu = resume.education
                new_edu = parsed_data.get('education')
                if old_edu != new_edu:
                    has_change = True
                    changes.append(f"学历: {old_edu} -> {new_edu}")
                    resume.education = new_edu

                old_edu_level = resume.education_level
                new_edu_level = parsed_data.get('education_level')
                if old_edu_level != new_edu_level:
                    has_change = True
                    changes.append(f"学历等级: {old_edu_level} -> {new_edu_level}")
                    resume.education_level = new_edu_level

                old_work_years = resume.work_years or 0
                new_work_years = parsed_data.get('work_years', 0)
                if old_work_years != new_work_years:
                    has_change = True
                    changes.append(f"工作年限: {old_work_years} -> {new_work_years}")
                    resume.work_years = new_work_years

                # 比较工作经历
                old_work_exp = resume.work_experience or []
                new_work_exp = parsed_data.get('work_experience', [])
                if old_work_exp != new_work_exp:
                    has_change = True
                    changes.append(f"工作经历: {len(old_work_exp)}条 -> {len(new_work_exp)}条")
                    resume.work_experience = new_work_exp

                # 比较项目经历
                old_proj_exp = resume.project_experience or []
                new_proj_exp = parsed_data.get('project_experience', [])
                if old_proj_exp != new_proj_exp:
                    has_change = True
                    changes.append(f"项目经历: {len(old_proj_exp)}条 -> {len(new_proj_exp)}条")
                    resume.project_experience = new_proj_exp

                # 比较教育背景
                old_edu_hist = resume.education_history or []
                new_edu_hist = parsed_data.get('education_history', [])
                if old_edu_hist != new_edu_hist:
                    has_change = True
                    changes.append(f"教育背景: {len(old_edu_hist)}条 -> {len(new_edu_hist)}条")
                    resume.education_history = new_edu_hist

                # 比较技能
                old_skills = resume.skills or []
                new_skills = parsed_data.get('skills', [])
                if old_skills != new_skills:
                    has_change = True
                    changes.append(f"技能: {len(old_skills)}个 -> {len(new_skills)}个")
                    resume.skills = new_skills

                old_skills_by_level = resume.skills_by_level or {}
                new_skills_by_level = parsed_data.get('skills_by_level', {})
                if old_skills_by_level != new_skills_by_level:
                    has_change = True
                    changes.append(f"技能分类: 已更新")
                    resume.skills_by_level = new_skills_by_level

                # 如果有变化，更新数据库
                if has_change:
                    resume.updated_at = datetime.now()
                    db.commit()
                    updated_count += 1

                    if idx % 20 == 0 or idx == total:
                        logger.info(
                            f"[{idx}/{total}] {resume.candidate_name or '未命名'}: "
                            f"更新 {len(changes)} 项"
                        )
                        for change in changes[:3]:  # 只显示前3项变化
                            logger.info(f"  - {change}")
                        if len(changes) > 3:
                            logger.info(f"  - ... 还有 {len(changes) - 3} 项变化")
                else:
                    no_change_count += 1

                # 定期显示进度（每100份显示一次，减少输出）
                if idx % 100 == 0:
                    logger.info(
                        f"进度: {idx}/{total} | "
                        f"已更新: {updated_count} | "
                        f"无变化: {no_change_count} | "
                        f"错误: {error_count}"
                    )

            except Exception as e:
                logger.error(f"处理简历 {resume.id} ({resume.candidate_name}) 时出错: {str(e)}")
                db.rollback()
                error_count += 1
                continue

        logger.info("\n" + "=" * 80)
        logger.info("全面重新解析完成！")
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
    logger.info("开始全面重新解析简历...\n")
    reparse_all_resumes()
