"""重新处理现有简历，提取技能熟练度"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser


def update_resume_skills():
    """更新所有简历的技能熟练度"""
    parser = ResumeParser()
    session = SessionLocal()

    try:
        # 查询所有有raw_text的简历
        result = session.execute(
            select(Resume).where(Resume.raw_text.isnot(None))
        )
        resumes = result.scalars().all()

        print(f"找到 {len(resumes)} 份需要更新的简历")

        updated_count = 0
        for i, resume in enumerate(resumes, 1):
            try:
                # 重新解析简历文本，提取熟练度
                skills_with_levels = parser._extract_skills_with_proficiency(
                    resume.raw_text or ""
                )

                # 合并所有技能（用于向后兼容）
                all_skills = (
                    skills_with_levels.get('expert', []) +
                    skills_with_levels.get('proficient', []) +
                    skills_with_levels.get('familiar', []) +
                    skills_with_levels.get('mentioned', [])
                )

                # 更新数据库
                resume.skills = all_skills
                resume.skills_by_level = skills_with_levels
                updated_count += 1

                expert_count = len(skills_with_levels.get('expert', []))
                proficient_count = len(skills_with_levels.get('proficient', []))
                familiar_count = len(skills_with_levels.get('familiar', []))
                mentioned_count = len(skills_with_levels.get('mentioned', []))

                print(f"[{i}/{len(resumes)}] 更新简历: {resume.candidate_name or '未知'} "
                      f"- 共{len(all_skills)}个技能 ({expert_count} 精通, {proficient_count} 熟悉, "
                      f"{familiar_count} 了解, {mentioned_count} 提及)")

                # 每10条提交一次
                if i % 10 == 0:
                    session.commit()

            except Exception as e:
                print(f"处理简历 {resume.id} 时出错: {e}")
                session.rollback()
                continue

        # 最终提交
        session.commit()
        print(f"\n完成！共更新 {updated_count} 份简历")

    finally:
        session.close()


if __name__ == "__main__":
    update_resume_skills()
