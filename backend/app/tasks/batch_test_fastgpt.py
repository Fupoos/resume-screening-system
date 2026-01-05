"""批��测试FastGPT评估"""
import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.agent_client import AgentClient


def batch_test():
    """批量测试FastGPT评估"""
    db = SessionLocal()

    try:
        # 选择3份简历进行测试
        resumes = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).limit(3).all()

        print("=" * 80)
        print("批量测试FastGPT评估")
        print("=" * 80)

        agent_client = AgentClient()

        for idx, resume in enumerate(resumes, 1):
            print(f"\n【简历 {idx}/{len(resumes)}】")
            print(f"ID: {resume.id}")
            print(f"姓名: {resume.candidate_name or '未知'}")
            print(f"学历: {resume.education or '未知'}")
            print(f"工作年限: {resume.work_years or 0}年")

            # 设置职位
            resume.job_category = "实施顾问"
            db.commit()

            # 调用Agent评估
            resume_data = {
                "candidate_name": resume.candidate_name,
                "phone": resume.phone,
                "email": resume.email,
                "education": resume.education,
                "work_years": resume.work_years,
                "skills": resume.skills or [],
                "raw_text": resume.raw_text,
            }

            print(f"正在调用FastGPT...")
            result = agent_client.evaluate_resume(
                job_title="实施顾问",
                city=resume.city,
                pdf_path=resume.file_path or "",
                resume_data=resume_data
            )

            # 分类
            score = result['score']
            if score >= 70:
                category = "可以发offer"
            elif score >= 40:
                category = "待定"
            else:
                category = "不合格"

            # 保存
            resume.agent_score = result['score']
            resume.agent_evaluation_id = result['evaluation_id']
            resume.screening_status = category
            resume.agent_evaluated_at = datetime.now()
            db.commit()

            # 显示结果
            if result['score'] >= 70:
                emoji = "🟢"
            elif result['score'] >= 40:
                emoji = "🟡"
            else:
                emoji = "🔴"

            print(f"✓ 评分: {result['score']}/100")
            print(f"✓ 分类: {emoji} {category}")

        print("\n" + "=" * 80)
        print("批量测试完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    batch_test()
