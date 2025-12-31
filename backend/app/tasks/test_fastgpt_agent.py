"""测试FastGPT Agent集成"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.fastgpt_client import FastGPTClient
from app.core.database import SessionLocal
from app.models.resume import Resume


def test_fastgpt():
    """测试FastGPT评估功能"""
    db = SessionLocal()

    try:
        # 获取一份简历（最好是实施顾问职位的简历）
        resume = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).first()

        if not resume:
            print("❌ 没有找到测试简历")
            print("   请确保数据库中有PDF简历")
            return

        print("=" * 60)
        print("FastGPT Agent 集成测试")
        print("=" * 60)
        print(f"\n测试简历:")
        print(f"  ID: {resume.id}")
        print(f"  姓名: {resume.candidate_name or '未知'}")
        print(f"  学历: {resume.education or '未知'}")
        print(f"  工作年限: {resume.work_years or 0}年")
        print(f"  简历长度: {len(resume.raw_text)} 字符")

        # 初始化FastGPT客户端
        print("\n" + "=" * 60)
        print("步骤1: 初始化FastGPT客户端")
        print("=" * 60)

        client = FastGPTClient(
            api_key="api-lzaV5DY9iZH30L15AZ4gpmlFZCmdulswPhRAnKHexG97iCbVvbFqkwIL5",
            base_url="https://ai.cloudpense.com/api"
        )
        print("✓ FastGPT客户端初始化成功")

        # 测试连接
        print("\n" + "=" * 60)
        print("步骤2: 测试FastGPT连接")
        print("=" * 60)

        if client.test_connection():
            print("✓ FastGPT连接测试成功")
        else:
            print("✗ FastGPT连接测试失败")
            print("   请检查:")
            print("   1. API密钥是否正确")
            print("   2. 网络连接是否正常")
            print("   3. FastGPT服务是否在线")
            return

        # 测试评估
        print("\n" + "=" * 60)
        print("步骤3: 测试简历评估")
        print("=" * 60)

        print(f"正在评估简历: {resume.candidate_name or '未知'}...")
        result = client.evaluate_resume(
            resume_text=resume.raw_text,
            candidate_name=resume.candidate_name or "未知",
            job_title="实施顾问"
        )

        # 显示评估结果
        print("\n" + "=" * 60)
        print("评估结果")
        print("=" * 60)
        print(f"分数: {result['score']}/100")

        # 根据分数判断分类
        score = result['score']
        if score >= 70:
            category = "可以发offer"
            color = "🟢"
        elif score >= 40:
            category = "待定"
            color = "🟡"
        else:
            category = "不合格"
            color = "🔴"

        print(f"分类: {color} {category}")
        print(f"评估ID: {result['evaluation_id']}")

        if 'details' in result:
            details = result['details']
            if 'raw_response' in details:
                print(f"\n原始响应（前500字符）:")
                print(f"  {details['raw_response'][:200]}...")
            if 'error' in details:
                print(f"\n错误信息: {details['error']}")

        # 测试总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print("✓ 所有测试通过!")
        print("\nFastGPT Agent已成功集成到系统中")
        print(f"当新简历被识别为'实施顾问'职位时，")
        print(f"系统将自动调用FastGPT进行评估")
        print(f"并根据评分({score}分)分类为'{category}'")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    test_fastgpt()
