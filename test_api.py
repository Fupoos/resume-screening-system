"""API测试脚本"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_list_jobs():
    """测试获取岗位列表"""
    print("\n=== 测试获取岗位列表 ===")
    response = requests.get(f"{BASE_URL}/api/v1/jobs/")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        jobs = response.json()
        print(f"找到 {len(jobs)} 个岗位:")
        for job in jobs:
            print(f"\n  - {job['name']} ({job['category']})")
            print(f"    ID: {job['id']}")
            print(f"    必备技能: {', '.join(job['required_skills'])}")
            print(f"    最低学历: {job['min_education']}")
            print(f"    最低经验: {job['min_work_years']}年")
        return jobs
    else:
        print(f"Error: {response.text}")
        return []


def test_match_resume():
    """测试简历匹配"""
    print("\n=== 测试简历匹配 ===")

    # Python后端工程师的ID
    job_id = "00000000-0000-0000-0000-000000000002"

    # 测试简历数据
    resume_data = {
        "candidate_name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@example.com",
        "education": "本科",
        "work_years": 3,
        "skills": ["Python", "FastAPI", "React", "MySQL", "Docker", "Git"],
        "job_id": job_id
    }

    print("候选人信息:")
    print(f"  姓名: {resume_data['candidate_name']}")
    print(f"  学历: {resume_data['education']}")
    print(f"  工作年限: {resume_data['work_years']}年")
    print(f"  技能: {', '.join(resume_data['skills'])}")

    response = requests.post(
        f"{BASE_URL}/api/v1/screening/match",
        json=resume_data
    )

    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n匹配结果:")
        print(f"  岗位: {result['job_name']}")
        print(f"  筛选结果: {result['screening_result']}")
        print(f"  总分: {result['match_score']}")
        print(f"  技能分数: {result['skill_score']}")
        print(f"  经验分数: {result['experience_score']}")
        print(f"  学历分数: {result['education_score']}")
        print(f"\n  匹配点:")
        for point in result['matched_points']:
            print(f"    ✓ {point}")
        if result['unmatched_points']:
            print(f"\n  不匹配点:")
            for point in result['unmatched_points']:
                print(f"    ✗ {point}")
        print(f"\n  建议: {result['suggestion']}")
    else:
        print(f"Error: {response.text}")


def test_hr_match():
    """测试HR岗位匹配"""
    print("\n=== 测试HR岗位匹配 ===")

    # HR专员的ID
    job_id = "00000000-0000-0000-0000-000000000001"

    # 测试简历数据
    resume_data = {
        "candidate_name": "李四",
        "phone": "13900139000",
        "email": "lisi@example.com",
        "education": "本科",
        "work_years": 2,
        "skills": ["招聘", "培训", "绩效管理", "HRIS系统", "薪酬管理"],
        "job_id": job_id
    }

    print("候选人信息:")
    print(f"  姓名: {resume_data['candidate_name']}")
    print(f"  学历: {resume_data['education']}")
    print(f"  工作年限: {resume_data['work_years']}年")
    print(f"  技能: {', '.join(resume_data['skills'])}")

    response = requests.post(
        f"{BASE_URL}/api/v1/screening/match",
        json=resume_data
    )

    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n匹配结果:")
        print(f"  岗位: {result['job_name']}")
        print(f"  筛选结果: {result['screening_result']}")
        print(f"  总分: {result['match_score']}")
        print(f"\n  建议: {result['suggestion']}")
    else:
        print(f"Error: {response.text}")


def test_finance_match():
    """测试财务岗位匹配"""
    print("\n=== 测试财务岗位匹配 ===")

    # 财务专员的ID
    job_id = "00000000-0000-0000-0000-000000000003"

    # 测试简历数据
    resume_data = {
        "candidate_name": "王五",
        "phone": "13700137000",
        "email": "wangwu@example.com",
        "education": "大专",
        "work_years": 1,
        "skills": ["Excel", "会计"],
        "job_id": job_id
    }

    print("候选人信息:")
    print(f"  姓名: {resume_data['candidate_name']}")
    print(f"  学历: {resume_data['education']}")
    print(f"  工作年限: {resume_data['work_years']}年")
    print(f"  技能: {', '.join(resume_data['skills'])}")

    response = requests.post(
        f"{BASE_URL}/api/v1/screening/match",
        json=resume_data
    )

    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n匹配结果:")
        print(f"  岗位: {result['job_name']}")
        print(f"  筛选结果: {result['screening_result']}")
        print(f"  总分: {result['match_score']}")
        print(f"\n  建议: {result['suggestion']}")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("简历智能初筛系统 - API测试")
    print("=" * 60)

    try:
        # 1. 健康检查
        test_health()

        # 2. 获取岗位列表
        jobs = test_list_jobs()

        # 3. 测试Python工程师匹配
        test_match_resume()

        # 4. 测试HR岗位匹配
        test_hr_match()

        # 5. 测试财务岗位匹配（应该显示REVIEW或REJECT）
        test_finance_match()

        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到服务器")
        print("请确保后端服务正在运行:")
        print("  cd Desktop/resume-screening-system")
        print("  docker-compose up -d")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
