"""筛选相关API路由

根据CLAUDE.md核心原则：
- 所有筛选结果只来自外部Agent评估
- 不提供手动匹配功能（已删除POST /match）
- GET /results只返回有agent_score的简历
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.screening_result import ScreeningResult
from app.models.resume import Resume
from app.models.job import Job
from app.services.university_classifier import classify_education_level

router = APIRouter()


@router.get("/results")
async def list_screening_results(
    resume_id: Optional[UUID] = Query(None, description="筛选简历ID"),
    job_id: Optional[UUID] = Query(None, description="筛选岗位ID"),
    result: Optional[str] = Query(None, description="筛选结果类型"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db)
):
    """获取筛选结果列表（只显示已配置FastGPT Agent的岗位类别）

    根据CLAUDE.md核心原则：
    - 只显示已配置Agent的岗位类别（目前只有实施顾问/consulting）
    - 已评估的简历：显示screening_results数据
    - 未评估的简历：显示为"待评估"(PENDING)
    """
    # 0. 🔴 新增：获取所有已配置FastGPT Agent的岗位类别
    agent_jobs = db.query(Job).filter(
        Job.is_active == True,
        Job.agent_type == 'fastgpt'
    ).all()

    # 使用Job的name（中文名称）来过滤简历，因为Resume.job_category存储的是中文名称
    agent_job_names = set(job.name for job in agent_jobs)

    if not agent_job_names:
        # 如果没有配置FastGPT Agent，返回空结果
        return {"total": 0, "results": []}

    # 1. 获取所有有效的PDF+正文简历，且job_category在已配置Agent的岗位中
    valid_resumes_query = db.query(Resume).filter(
        Resume.file_type == 'pdf',
        Resume.raw_text.isnot(None),
        Resume.raw_text != '',
        Resume.job_category.in_(agent_job_names)  # 🔴 新增：只显示已配置Agent的岗位
    )

    # 可选过滤：按简历ID
    if resume_id:
        valid_resumes_query = valid_resumes_query.filter(Resume.id == resume_id)

    valid_resumes = valid_resumes_query.all()

    if not valid_resumes:
        return {"total": 0, "results": []}

    valid_resume_ids = [r.id for r in valid_resumes]

    # 2. 获取screening_results（已评估的简历）
    screenings_query = db.query(ScreeningResult).filter(
        ScreeningResult.resume_id.in_(valid_resume_ids)
    )

    # 可选过滤：按岗位ID和筛选结果
    if job_id:
        screenings_query = screenings_query.filter(ScreeningResult.job_id == job_id)
    if result:
        screenings_query = screenings_query.filter(ScreeningResult.screening_result == result.upper())

    all_screenings = screenings_query.order_by(ScreeningResult.created_at.desc()).all()

    # 过滤掉明显异常的简历名字
    import re
    def is_valid_name(name: str) -> bool:
        """检查名字是否有效（放宽条件）"""
        if not name:
            return False

        # 排除明显的无效名字
        invalid_patterns = [
            r'^[0-9a-fA-F-]{36}$',  # UUID格式

            # 常见简历标题和关键词（完整匹配或包含）
            r'实习|工作|项目|教育|技能|求职|个人|基本信息|联系方式',

            # 学历相关
            r'双一流|211|985|学士|硕士|博士|本科|大专|高中|中专',

            # 证书相关
            r'证书|资格证|获得证书|职业资格',

            # 成果相关
            r'成果|业绩|成就|工作成果|项目成果',

            # 自我评价相关
            r'自我评价|个人简介|个人总结|优势特长',

            # 其他常见无效词
            r'专业技能|专业特长|核心竞争力|主修课程|语言能力',

            # 🔴 个人属性相关（新增）
            r'身高|体重|生日|年龄|性别|民族|婚姻|健康状况|政治面貌',
            r'籍贯|出生地|现居地|现居地址|联系电话|电子邮箱|邮箱地址|电话号码',
            r'求职意向|期望薪资|到岗时间|工作性质|入职时间|从业背景',
            r'联系方式|手机号码|手机号|邮箱|邮编|通讯地址',

            # 🔴 其他常见无效词（新增）
            r'主修|外语水平|计算机能力|兴趣爱好|特长爱好',
            r'在校经历|社会实践|校园活动|获奖情况',
        ]
        for pattern in invalid_patterns:
            if re.search(pattern, name):
                return False

        # 长度检查：放宽到1-15个字符（支持复姓和少数民族名字）
        if len(name) < 1 or len(name) > 15:
            return False

        # 排除纯英文（但保留中英混合）
        if re.match(r'^[a-zA-Z\s]+$', name):
            return False

        return True

    # 4. 构建有效简历ID集合（名字正常的）
    valid_resume_ids_clean = []
    resume_dict = {}  # {resume_id: resume_obj}

    for resume in valid_resumes:
        if (resume.candidate_name and
            resume.candidate_name != '' and
            is_valid_name(resume.candidate_name)):
            valid_resume_ids_clean.append(resume.id)
            resume_dict[resume.id] = resume

    # 5. 过滤筛选结果，只保留名字正常的
    all_screenings = [s for s in all_screenings if s.resume_id in valid_resume_ids_clean]

    # 6. 按简历分组，取前2个最佳匹配
    resume_groups = {}
    resume_ids_with_screenings = set()  # 记录有screening_results的简历ID

    for screening in all_screenings:
        rid = screening.resume_id
        resume_ids_with_screenings.add(rid)
        if rid not in resume_groups:
            resume_groups[rid] = []
        resume_groups[rid].append(screening)

    # 每个简历只保留前2个最佳匹配
    for rid in resume_groups:
        resume_groups[rid].sort(key=lambda x: x.agent_score or 0, reverse=True)
        resume_groups[rid] = resume_groups[rid][:2]

    # 7. 展平已评估的筛选结果
    evaluated_results = []
    for screenings in resume_groups.values():
        evaluated_results.extend(screenings)

    # 8. 🔴 新增：为未评估的简历补充"待评估"记录
    pending_results = []
    for resume_id in valid_resume_ids_clean:
        if resume_id not in resume_ids_with_screenings:
            resume = resume_dict[resume_id]

            # 🔴 新增：从简历文本中实时分类学历等级
            education_level = resume.education_level
            if not education_level and resume.raw_text:
                education_level = classify_education_level(resume.raw_text)

            # 获取技能标签（取前3个）
            skills_list = resume.skills or []
            if isinstance(skills_list, list):
                skills_display = skills_list[:3]
            else:
                skills_display = []

            # 创建一个待评估记录（不保存到数据库）
            pending_record = {
                "id": None,  # 没有screening_result ID
                "resume_id": str(resume_id),
                "candidate_name": resume.candidate_name,
                "candidate_email": resume.email,
                "candidate_phone": resume.phone,
                "candidate_education": resume.education,
                "education_level": education_level,  # 🔴 新增：学历等级分类
                "job_id": None,  # 未分配岗位
                "job_name": resume.job_category or "待分类",
                "job_category": resume.job_category or "unknown",
                "agent_score": None,
                "screening_result": "PENDING",  # 待评估
                "matched_points": [],
                "unmatched_points": [],
                "suggestion": "待评估" if resume.agent_score is None else "未配置Agent",
                "evaluated": False,  # 🔴 标记为未评估
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "work_years": resume.work_years,  # 🔴 新增：工作年限
                "work_experience": resume.work_experience,  # 🔴 新增：工作经历
                "skills": skills_display  # 🔴 新增：技能标签（前3个）
            }
            pending_results.append(pending_record)

    # 9. 转换已评估的筛选结果为响应格式
    evaluated_results_formatted = []
    for screening in evaluated_results:
        resume = resume_dict.get(screening.resume_id)
        if not resume:
            continue

        # 获取岗位信息（从数据库）
        job = db.query(Job).filter(Job.id == screening.job_id).first()

        # 🔴 新增：从简历文本中实时分类学历等级（如果数据库中没有）
        education_level = resume.education_level
        if not education_level and resume.raw_text:
            education_level = classify_education_level(resume.raw_text)

        # 获取技能标签（取前3个）
        skills_list = resume.skills or []
        if isinstance(skills_list, list):
            skills_display = skills_list[:3]
        else:
            skills_display = []

        evaluated_results_formatted.append({
            "id": str(screening.id),
            "resume_id": str(screening.resume_id),
            "candidate_name": resume.candidate_name,
            "candidate_email": resume.email,
            "candidate_phone": resume.phone,
            "candidate_education": resume.education,
            "education_level": education_level,  # 🔴 新增：学历等级分类
            "job_id": str(screening.job_id),
            "job_name": job.name if job else "未知岗位",
            "job_category": job.name if job else (resume.job_category or "unknown"),  # 🔴 修复：返回中文岗位类别
            "agent_score": screening.agent_score,
            "screening_result": screening.screening_result,
            "matched_points": screening.matched_points or [],
            "unmatched_points": screening.unmatched_points or [],
            "suggestion": screening.suggestion,
            "evaluated": True,  # 🔴 标记为已评估
            "created_at": screening.created_at.isoformat() if screening.created_at else None,
            "work_years": resume.work_years,  # 🔴 新增：工作年限
            "work_experience": resume.work_experience,  # 🔴 新增：工作经历
            "skills": skills_display  # 🔴 新增：技能标签（前3个）
        })

    # 10. 合并已评估和未评估的结果
    all_results = evaluated_results_formatted + pending_results

    # 11. 分页
    total = len(all_results)
    paginated_results = all_results[skip:skip + limit]

    return {
        "total": total,
        "results": paginated_results
    }


@router.get("/result/{screening_id}")
async def get_screening_result(screening_id: UUID, db: Session = Depends(get_db)):
    """获取筛选结果详情"""
    screening = db.query(ScreeningResult).filter(ScreeningResult.id == screening_id).first()

    if not screening:
        raise HTTPException(status_code=404, detail="筛选结果不存在")

    # 获取简历信息
    resume = db.query(Resume).filter(Resume.id == screening.resume_id).first()

    # 获取岗位信息（从数据库）
    job = db.query(Job).filter(Job.id == screening.job_id).first()

    return {
        "id": str(screening.id),
        "resume_id": str(screening.resume_id),
        "candidate_name": resume.candidate_name if resume else "未知",
        "candidate_email": resume.email if resume else None,
        "candidate_phone": resume.phone if resume else None,
        "candidate_education": resume.education if resume else None,
        "candidate_work_years": resume.work_years if resume else None,
        "candidate_skills": resume.skills if resume else [],
        "job_id": str(screening.job_id),
        "job_name": job.name if job else "未知岗位",
        "job_category": job.category if job else "unknown",
        "agent_score": screening.agent_score,
        "screening_result": screening.screening_result,
        "matched_points": screening.matched_points or [],
        "unmatched_points": screening.unmatched_points or [],
        "suggestion": screening.suggestion,
        "created_at": screening.created_at.isoformat() if screening.created_at else None
    }
