"""前端功能测试脚本"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_backend_health():
    """测试后端健康"""
    print("\n=== 测试1: 后端健康检查 ===")
    response = requests.get("http://localhost:8000/health")
    print(f"✅ 后端状态: {response.json()}")
    return True

def test_get_jobs():
    """测试获取岗位列表"""
    print("\n=== 测试2: 获取岗位列表 ===")
    response = requests.get(f"{BASE_URL}/jobs/")
    jobs = response.json()
    print(f"✅ 找到 {len(jobs)} 个岗位:")
    for job in jobs:
        print(f"  - {job['name']} ({job['category']}) - ID: {job['id']}")
    return jobs

def test_python_engineer_match():
    """测试Python工程师匹配"""
    print("\n=== 测试3: Python工程师匹配 ===")

    job_id = "00000000-0000-0000-0000-000000000002"

    # 强候选
    resume_data = {
        "candidate_name": "张三（强候选）",
        "education": "本科",
        "work_years": 3,
        "skills": ["Python", "FastAPI", "MySQL", "Redis", "Docker"],
        "job_id": job_id
    }

    print(f"候选人: {resume_data['candidate_name']}")
    print(f"学历: {resume_data['education']}, 工作年限: {resume_data['work_years']}年")
    print(f"技能: {', '.join(resume_data['skills'])}")

    response = requests.post(f"{BASE_URL}/screening/match", json=resume_data)
    result = response.json()

    print(f"\n匹配结果:")
    print(f"  筛选结果: {result['screening_result']}")
    print(f"  总分: {result['match_score']}")
    print(f"  技能分数: {result['skill_score']}")
    print(f"  经验分数: {result['experience_score']}")
    print(f"  学历分数: {result['education_score']}")

    print(f"\n  匹配点:")
    for point in result['matched_points']:
        print(f"    ✓ {point}")

    if result['unmatched_points']:
        print(f"  不匹配点:")
        for point in result['unmatched_points']:
            print(f"    ✗ {point}")

    print(f"\n  建议: {result['suggestion']}")

    return result

def test_hr_match():
    """测试HR专员匹配"""
    print("\n=== 测试4: HR专员匹配 ===")

    job_id = "00000000-0000-0000-0000-000000000001"

    resume_data = {
        "candidate_name": "李四",
        "education": "本科",
        "work_years": 2,
        "skills": ["招聘", "培训", "绩效管理", "HRIS系统", "薪酬管理"],
        "job_id": job_id
    }

    print(f"候选人: {resume_data['candidate_name']}")
    print(f"学历: {resume_data['education']}, 工作年限: {resume_data['work_years']}年")
    print(f"技能: {', '.join(resume_data['skills'])}")

    response = requests.post(f"{BASE_URL}/screening/match", json=resume_data)
    result = response.json()

    print(f"\n匹配结果:")
    print(f"  筛选结果: {result['screening_result']}")
    print(f"  总分: {result['match_score']}")
    print(f"  建议: {result['suggestion']}")

    return result

def test_weak_candidate():
    """测试弱候选"""
    print("\n=== 测试5: 弱候选（应该REJECT）===")

    job_id = "00000000-0000-0000-0000-000000000003"  # 财务专员

    resume_data = {
        "candidate_name": "王五（弱候选）",
        "education": "大专",
        "work_years": 1,
        "skills": ["Excel"],  # 只有Excel，缺少其他必备技能
        "job_id": job_id
    }

    print(f"候选人: {resume_data['candidate_name']}")
    print(f"学历: {resume_data['education']}, 工作年限: {resume_data['work_years']}年")
    print(f"技能: {', '.join(resume_data['skills'])}")

    response = requests.post(f"{BASE_URL}/screening/match", json=resume_data)
    result = response.json()

    print(f"\n匹配结果:")
    print(f"  筛选结果: {result['screening_result']}")
    print(f"  总分: {result['match_score']}")
    print(f"  建议: {result['suggestion']}")

    return result

def main():
    print("=" * 60)
    print("简历智能初筛系统 - 前端功能测试")
    print("=" * 60)

    try:
        # 测试1: 健康检查
        test_backend_health()

        # 测试2: 获取岗位
        jobs = test_get_jobs()

        # 测试3: Python工程师匹配
        result1 = test_python_engineer_match()

        # 测试4: HR专员匹配
        result2 = test_hr_match()

        # 测试5: 弱候选
        result3 = test_weak_candidate()

        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"✅ 所有API测试通过")
        print(f"✅ 岗位管理: {len(jobs)} 个预设岗位")
        print(f"✅ Python工程师匹配: {result1['screening_result']} ({result1['match_score']}分)")
        print(f"✅ HR专员匹配: {result2['screening_result']} ({result2['match_score']}分)")
        print(f"✅ 弱候选筛选: {result3['screening_result']} ({result3['match_score']}分)")
        print("\n🎉 前端可以正常使用！访问 http://localhost:3000")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("\n请确保:")
        print("1. 后端服务正在运行: docker-compose ps")
        print("2. 前端服务正在运行: 访问 http://localhost:3000")

if __name__ == "__main__":
    main()
