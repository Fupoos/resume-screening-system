"""批量更新现有简历的技能"""
import sys
sys.path.append('/app')

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_resume_skills():
    """更新所有简历的技能"""
    db = SessionLocal()
    parser = ResumeParser()

    try:
        # 获取所有有raw_text但skills为空的简历
        resumes = db.query(Resume).filter(
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).all()

        logger.info(f"找到 {len(resumes)} 份有raw_text的简历")

        updated_count = 0
        for idx, resume in enumerate(resumes):
            try:
                # 检查是否需要更新
                if not resume.skills or len(resume.skills) == 0:
                    # 从raw_text提取技能
                    text = resume.raw_text[:10000]  # 使用前10000字符
                    skills = parser._extract_skills(text)

                    # 更新数据库
                    resume.skills = skills
                    db.commit()

                    updated_count += 1

                    if (idx + 1) % 50 == 0:
                        logger.info(f"已处理 {idx + 1}/{len(resumes)} 份简历")

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {e}")
                db.rollback()
                continue

        logger.info(f"完成！共更新了 {updated_count} 份简历的技能")
        return {"updated": updated_count, "total": len(resumes)}

    except Exception as e:
        logger.error(f"更新失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    result = update_resume_skills()
    print(f"\n更新结果: {result}")
