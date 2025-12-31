"""测试完整的FastGPT评估流程"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.agent_client import AgentClient
from app.services.screening_classifier import ScreeningClassifier


def test_full_workflow():
    """测试完整的评估流程"""
    db = SessionLocal()

    try:
        # 选择一份简历进行测试
        resume = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).first()

        if not resume:
            print("❌ 没有找到测试简历")
            return

        print("=" * 80)
        print("FastGPT 完整评估流程测试")
        print("=" * 80)

        print(f"\n【测试简历】")
        print(f"  ID: {resume.id}")
        print(f"  姓名: {resume.candidate_name or '未知'}")
        print(f"  学历: {resume.education or '未知'}")
        print(f"  工作年限: {resume.work_years or 0}年")
        print(f"  城市: {resume.city or '未知'}")
        print(f"  当前职位分类: {resume.job_category or '未分类'}")
        print(f"  当前Agent评分: {resume.agent_score or '未评估'}")

        # 模拟设置为实施顾问职位
        print("\n" + "=" * 80)
        print("步骤1: 设置职位为'实施顾问'")
        print("=" * 80)

        resume.job_category = "实施顾问"
        db.commit()
        print(f"✓ 已将简历 {resume.candidate_name or '未知'} 设置为'实施顾问'职位")

        # 调用AgentClient进行评估
        print("\n" + "=" * 80)
        print("步骤2: 调用Agent进行评估")
        print("=" * 80)

        agent_client = AgentClient()

        resume_data = {
            "candidate_name": resume.candidate_name,
            "phone": resume.phone,
            "email": resume.email,
            "education": resume.education,
            "work_years": resume.work_years,
            "skills": resume.skills or [],
            "raw_text": resume.raw_text,
        }

        print(f"正在调用FastGPT Agent评估...")
        result = agent_client.evaluate_resume(
            job_title="实施顾问",
            city=resume.city,
            pdf_path=resume.file_path or "",
            resume_data=resume_data
        )

        # 显示评估结果
        print(f"\n✓ Agent评估完成")
        print(f"  评分: {result['score']}/100")
        print(f"  评估ID: {result['evaluation_id']}")
        if 'error' in result.get('details', {}):
            print(f"  错误: {result['details']['error']}")

        # 使用ScreeningClassifier进行分类
        print("\n" + "=" * 80)
        print("步骤3: 根据评分进行分类")
        print("=" * 80)

        classifier = ScreeningClassifier()
        category = classifier.classify(result['score'])

        print(f"✓ 分类完成: {category}")

        # 更新简历的评估信息
        print("\n" + "=" * 80)
        print("步骤4: 保存评估结果")
        print("=" * 80)

        resume.agent_score = result['score']
        resume.agent_evaluation_id = result['evaluation_id']
        resume.screening_status = category
        db.commit()

        print(f"✓ 评估结果已保存到数据库")
        print(f"  agent_score: {resume.agent_score}")
        print(f"  screening_status: {resume.screening_status}")

        # 总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)

        # 根据分数显示emoji
        score = result['score']
        if score >= 70:
            emoji = "🟢"
            status_desc = "可以发offer"
        elif score >= 40:
            emoji = "🟡"
            status_desc = "待定"
        else:
            emoji = "🔴"
            status_desc = "不合格"

        print(f"✅ 完整流程测试成功!")
        print(f"\n候选人: {resume.candidate_name or '未知'}")
        print(f"职位: 实施顾问")
        print(f"FastGPT评分: {score}/100")
        print(f"筛选结果: {emoji} {category} ({status_desc})")
        print(f"\n评估已保存到数据库，可以在前端'筛选结果'页面查看")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    test_full_workflow()
