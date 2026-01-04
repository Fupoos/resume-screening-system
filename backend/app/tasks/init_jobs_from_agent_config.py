"""从agent_config.py同步岗位到数据库

使用方法：
    docker-compose exec backend python3 -m app.tasks.init_jobs_from_agent_config
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.job import Job
from app.core.agent_config import AGENT_ENDPOINTS
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 7个岗位的默认配置
JOB_DEFAULTS = {
    "Java开发": {
        "category": "software",
        "description": "负责Java后端系统开发",
        "required_skills": ["Java", "Spring Boot"],
        "preferred_skills": ["MySQL", "Redis", "Docker"],
        "min_work_years": 2,
        "min_education": "本科",
    },
    "销售总监": {
        "category": "sales",
        "description": "负责销售团队管理和业务拓展",
        "required_skills": ["销售", "团队管理"],
        "preferred_skills": ["谈判", "CRM", "战略规划"],
        "min_work_years": 5,
        "min_education": "本科",
    },
    "自动化测试": {
        "category": "software",
        "description": "负责自动化测试框架搭建和维护",
        "required_skills": ["Python", "Selenium"],
        "preferred_skills": ["Jenkins", "CI/CD", "Pytest"],
        "min_work_years": 2,
        "min_education": "本科",
    },
    "市场运营": {
        "category": "marketing",
        "description": "负责市场推广和运营活动",
        "required_skills": ["市场营销", "内容运营"],
        "preferred_skills": ["数据分析", "SEO", "新媒体"],
        "min_work_years": 1,
        "min_education": "本科",
    },
    "前端开发": {
        "category": "software",
        "description": "负责前端页面开发",
        "required_skills": ["JavaScript", "React"],
        "preferred_skills": ["TypeScript", "Vue", "CSS"],
        "min_work_years": 2,
        "min_education": "本科",
    },
    "产品经理": {
        "category": "product",
        "description": "负责产品规划和需求分析",
        "required_skills": ["产品设计", "需求分析"],
        "preferred_skills": ["Axure", "数据分析", "项目管理"],
        "min_work_years": 2,
        "min_education": "本科",
    },
    "实施顾问": {
        "category": "consulting",
        "description": "负责产品实施和客户培训",
        "required_skills": ["SQL", "客户沟通"],
        "preferred_skills": ["项目管理", "培训", "需求分析"],
        "min_work_years": 2,
        "min_education": "本科",
    },
}


def sync_jobs_from_agent_config():
    """从agent_config.py同步7个岗位到数据库"""
    db = SessionLocal()

    try:
        logger.info("开始从agent_config.py同步岗位...")

        # 遍历AGENT_ENDPOINTS，提取岗位名称
        synced_count = 0
        skipped_count = 0

        for key, config in AGENT_ENDPOINTS.items():
            # key格式: "Java开发_default", "销售总监_default"等
            if not key.endswith("_default"):
                continue

            # 提取岗位名称（去掉"_default"后缀）
            job_name = key[:-8]  # 去掉最后8个字符"_default"

            # 检查是否已存在
            existing_job = db.query(Job).filter(Job.name == job_name).first()
            if existing_job:
                logger.info(f"  ⊙ 跳过已存在的岗位: {job_name}")
                skipped_count += 1
                continue

            # 获取默认配置
            defaults = JOB_DEFAULTS.get(job_name, {})

            # 确定Agent类型
            agent_type = config.get("type", "http")

            # 创建新岗位
            new_job = Job(
                id=uuid.uuid4(),
                name=job_name,
                category=defaults.get("category", "other"),
                description=defaults.get("description", f"{job_name}岗位"),
                required_skills=defaults.get("required_skills", []),
                preferred_skills=defaults.get("preferred_skills", []),
                min_work_years=defaults.get("min_work_years", 0),
                min_education=defaults.get("min_education", "大专"),
                skill_weight=50,
                experience_weight=30,
                education_weight=20,
                pass_threshold=70,
                review_threshold=50,
                # Agent配置
                agent_type=agent_type,
                agent_url=config.get("url"),
                agent_timeout=config.get("timeout", 30),
                agent_retry=config.get("retry", 3),
                is_active=True,
            )

            db.add(new_job)
            db.commit()
            db.refresh(new_job)

            logger.info(f"  ✅ 同步岗位: {job_name} (ID: {new_job.id}, Agent类型: {agent_type})")
            synced_count += 1

        logger.info("\n" + "=" * 80)
        logger.info(f"同步完成！")
        logger.info(f"  新增岗位: {syncied_count} 个")
        logger.info(f"  跳过岗位: {skipped_count} 个")
        logger.info("=" * 80)

        # 显示当前所有岗位
        all_jobs = db.query(Job).filter(Job.is_active == True).all()
        logger.info(f"\n当前数据库中共有 {len(all_jobs)} 个岗位：")
        for job in all_jobs:
            logger.info(f"  - {job.name} ({job.category}) - Agent: {job.agent_type}")

    except Exception as e:
        logger.error(f"同步失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始从agent_config.py同步岗位到数据库...\n")
    sync_jobs_from_agent_config()
