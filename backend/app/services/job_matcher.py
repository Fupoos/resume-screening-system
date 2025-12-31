"""岗位匹配服务 - 实现4种岗位类型的规则匹配引擎"""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class JobMatcher:
    """岗位匹配器 - 基于规则的匹配引擎"""

    def __init__(self):
        """初始化匹配器"""
        # 导入语义匹配器
        from app.services.skill_matcher import SemanticSkillMatcher
        self.semantic_matcher = SemanticSkillMatcher()

        # 预设4种岗位的默认配置
        self.job_presets = {
            'hr': {
                'name': 'HR岗位',
                'required_skills': ['招聘', '培训', '绩效管理', '员工关系'],
                'preferred_skills': ['HRIS系统', '薪酬管理', '劳动合同', '人力资源'],
                'min_education': '大专',
                'min_work_years': 1,
                'education_order': ['博士', '硕士', '本科', '大专'],
                'skill_weight': 0.5,
                'experience_weight': 0.3,
                'education_weight': 0.2,
                'pass_threshold': 70,
                'review_threshold': 50
            },
            'software': {
                'name': '软件开发岗位',
                'required_skills': ['Python', 'Java', 'JavaScript', 'Go'],
                'preferred_skills': ['React', 'Vue', 'Django', 'Flask', 'FastAPI', 'MySQL', 'Redis', 'Docker'],
                'min_education': '本科',
                'min_work_years': 2,
                'education_order': ['博士', '硕士', '本科', '大专'],
                'skill_weight': 0.5,
                'experience_weight': 0.3,
                'education_weight': 0.2,
                'pass_threshold': 70,
                'review_threshold': 50
            },
            'finance': {
                'name': '财务岗位',
                'required_skills': ['财务报表', '会计', 'Excel', '财务软件'],
                'preferred_skills': ['税务', '审计', 'SAP', '成本管理', '预算管理'],
                'min_education': '大专',
                'min_work_years': 2,
                'education_order': ['博士', '硕士', '本科', '大专'],
                'skill_weight': 0.5,
                'experience_weight': 0.3,
                'education_weight': 0.2,
                'pass_threshold': 70,
                'review_threshold': 50
            },
            'sales': {
                'name': '销售岗位',
                'required_skills': ['销售', '客户开发', '谈判', 'CRM'],
                'preferred_skills': ['市场', '业务', '业绩目标', '客户维护'],
                'min_education': '大专',
                'min_work_years': 1,
                'education_order': ['博士', '硕士', '本科', '大专'],
                'skill_weight': 0.5,
                'experience_weight': 0.3,
                'education_weight': 0.2,
                'pass_threshold': 70,
                'review_threshold': 50
            }
        }

    def match(
        self,
        resume: Dict,
        job: Dict,
        custom_rules: Optional[Dict] = None
    ) -> Dict:
        """匹配简历与岗位

        Args:
            resume: 简历信息（解析后的）
            job: 岗位信息
            custom_rules: 自定义规则（可选）

        Returns:
            匹配结果
        """
        # 获取岗位配置
        job_category = job.get('category', 'software')

        # 如果是预设岗位类型，使用预设配置
        if job_category in self.job_presets:
            job_config = self.job_presets[job_category]
        else:
            # 使用自定义配置
            job_config = {
                'required_skills': job.get('required_skills', []),
                'preferred_skills': job.get('preferred_skills', []),
                'min_education': job.get('min_education', '大专'),
                'min_work_years': job.get('min_work_years', 0),
                'education_order': ['博士', '硕士', '本科', '大专'],
                'skill_weight': job.get('skill_weight', 50) / 100,
                'experience_weight': job.get('experience_weight', 30) / 100,
                'education_weight': job.get('education_weight', 20) / 100,
                'pass_threshold': job.get('pass_threshold', 70),
                'review_threshold': job.get('review_threshold', 50)
            }

        # 如果有自定义规则，覆盖默认配置
        if custom_rules:
            job_config.update(custom_rules)

        # 获取skills_by_level（如果可用）
        skills_by_level = resume.get('skills_by_level', {})

        # 计算各项分数
        skill_score, skill_details = self._calculate_skill_score(
            resume.get('skills', []),
            job_config['required_skills'],
            job_config['preferred_skills'],
            skills_by_level  # 新参数：传递熟练度数据
        )

        experience_score, experience_details = self._calculate_experience_score(
            resume.get('work_years', 0),
            job_config['min_work_years']
        )

        education_score, education_details = self._calculate_education_score(
            resume.get('education', ''),
            job_config['min_education'],
            job_config['education_order']
        )

        # 计算总分
        match_score = int(
            skill_score * job_config['skill_weight'] +
            experience_score * job_config['experience_weight'] +
            education_score * job_config['education_weight']
        )

        # 确定筛选结果
        if match_score >= job_config['pass_threshold']:
            screening_result = 'PASS'
        elif match_score >= job_config['review_threshold']:
            screening_result = 'REVIEW'
        else:
            screening_result = 'REJECT'

        # 生成匹配详情
        matched_points = []
        unmatched_points = []

        # 技能匹配点
        if skill_details['matched_required']:
            matched_points.append(f"必备技能匹配: {', '.join(skill_details['matched_required'])}")
        if skill_details['matched_preferred']:
            matched_points.append(f"加分技能: {', '.join(skill_details['matched_preferred'])}")

        if skill_details['unmatched_required']:
            unmatched_points.append(f"缺少必备技能: {', '.join(skill_details['unmatched_required'])}")

        # 经验匹配点
        if experience_details['meets_requirement']:
            matched_points.append(f"工作经验满足要求 ({resume.get('work_years', 0)}年)")
        else:
            unmatched_points.append(f"工作经验不足 ({resume.get('work_years', 0)}年 < {job_config['min_work_years']}年)")

        # 学历匹配点
        if education_details['meets_requirement']:
            matched_points.append(f"学历满足要求 ({resume.get('education', '未知')})")
        else:
            unmatched_points.append(f"学历不满足要求 ({resume.get('education', '未知')} < {job_config['min_education']})")

        return {
            'match_score': match_score,
            'skill_score': skill_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'screening_result': screening_result,
            'matched_points': matched_points,
            'unmatched_points': unmatched_points,
            'match_details': {
                'skill_details': skill_details,
                'experience_details': experience_details,
                'education_details': education_details
            },
            'confidence': 0.85,  # 基于规则的置信度
            'suggestion': self._generate_suggestion(screening_result, matched_points, unmatched_points)
        }

    def _calculate_skill_score(
        self,
        resume_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str],
        skills_by_level: Optional[Dict[str, List[str]]] = None
    ) -> tuple:
        """计算技能分数 - 改进版（OR逻辑 + 熟练度加权）

        Args:
            resume_skills: 简历技能列表
            required_skills: 必备技能列表
            preferred_skills: ���分技能列表
            skills_by_level: 按熟练度分类的技能（可选）

        Returns:
            (分数, 详细信息)
        """
        from typing import Dict, List, Optional

        # 标准化
        resume_skills_lower = [s.lower() for s in resume_skills]
        required_skills_lower = [s.lower() for s in required_skills]
        preferred_skills_lower = [s.lower() for s in preferred_skills]

        matched_required = []
        matched_preferred = []
        unmatched_required = []
        required_match_scores = {}  # skill -> score (0-100)

        # 辅助函数：查找技能及熟练度
        def find_skill_with_proficiency(skill: str) -> tuple:
            """返回 (found, proficiency_level)"""
            skill_lower = skill.lower()

            if skills_by_level:
                for level in ['expert', 'proficient', 'familiar', 'mentioned']:
                    for resume_skill in skills_by_level.get(level, []):
                        if resume_skill.lower() == skill_lower:
                            return True, level
                return False, None
            else:
                # 向后兼容：仅检查存在性
                return skill_lower in resume_skills_lower, None

        # 匹配required skills（带熟练度评分）
        for skill in required_skills:
            found, proficiency = find_skill_with_proficiency(skill)

            if found:
                matched_required.append(skill)

                # 根据熟练度计算分数
                if proficiency == 'expert':
                    score = 100
                elif proficiency == 'proficient':
                    score = 80
                elif proficiency == 'familiar':
                    score = 60
                elif proficiency == 'mentioned':
                    score = 40
                else:
                    score = 70  # 默认

                required_match_scores[skill] = score
            else:
                unmatched_required.append(skill)
                required_match_scores[skill] = 0

        # 对未匹配的 required skills 尝试语义匹配
        if unmatched_required:
            semantic_matches, semantic_scores = self.semantic_matcher.find_semantic_matches(
                unmatched_required,
                resume_skills,
                skills_by_level or {}
            )

            # 添加语义匹配结果
            for skill, confidence in semantic_scores.items():
                if skill in unmatched_required:
                    matched_required.append(f"{skill} (semantic)")
                    # 语义匹配分数基于置信度，上限70%
                    semantic_score = int(confidence * 70)
                    required_match_scores[skill] = semantic_score
                    unmatched_required.remove(skill)

        # 匹配preferred skills（任意匹配 = 满分）
        for skill in preferred_skills:
            found, _ = find_skill_with_proficiency(skill)
            if found:
                matched_preferred.append(skill)

        # 计算总分
        if required_skills:
            # OR逻辑：平均值而非全部必须
            required_score = sum(required_match_scores.values()) / len(required_skills)
            required_score = (required_score / 100) * 60  # 缩放到60分
        else:
            required_score = 60

        if preferred_skills:
            preferred_score = (len(matched_preferred) / len(preferred_skills)) * 40
        else:
            preferred_score = 0

        total_score = int(required_score + preferred_score)

        details = {
            'matched_required': matched_required,
            'matched_preferred': matched_preferred,
            'unmatched_required': unmatched_required,
            'total_required': len(required_skills),
            'total_preferred': len(preferred_skills),
            'required_match_scores': required_match_scores,  # 新增：详细分数
        }

        return total_score, details

    def _calculate_experience_score(
        self,
        work_years: int,
        min_work_years: int
    ) -> tuple:
        """计算经验分数

        Returns:
            (分数, 详细信息)
        """
        if work_years >= min_work_years:
            # 满足要求，基础分100
            # 超出要求可以加分，最高不超过100
            excess_years = work_years - min_work_years
            bonus = min(excess_years * 5, 20)  # 每多一年加5分，最多加20分
            score = min(100 + bonus, 100)
            meets_requirement = True
        else:
            # 不满足要求，按比例扣分
            if min_work_years > 0:
                score = int((work_years / min_work_years) * 100)
            else:
                score = 100
            meets_requirement = False

        details = {
            'work_years': work_years,
            'min_work_years': min_work_years,
            'meets_requirement': meets_requirement
        }

        return score, details

    def _calculate_education_score(
        self,
        education: str,
        min_education: str,
        education_order: List[str]
    ) -> tuple:
        """计算学历分数

        Returns:
            (分数, 详细信息)
        """
        # 处理None或空字符串
        if not education:
            education = ''

        # 确定学历等级
        education_level = len(education_order)  # 默认最低
        min_education_level = len(education_order)

        for i, edu in enumerate(education_order):
            if edu in education:
                education_level = i
            if edu in min_education:
                min_education_level = i

        # 计算分数
        if education_level <= min_education_level:
            score = 100
            meets_requirement = True
        else:
            # 学历不满足，扣分
            gap = education_level - min_education_level
            score = max(100 - gap * 30, 0)  # 每差一级扣30分
            meets_requirement = False

        details = {
            'education': education,
            'min_education': min_education,
            'meets_requirement': meets_requirement
        }

        return score, details

    def _generate_suggestion(
        self,
        screening_result: str,
        matched_points: List[str],
        unmatched_points: List[str]
    ) -> str:
        """生成建议说明"""
        if screening_result == 'PASS':
            return f"候选人符合岗位要求，建议进入面试环节。亮点: {'; '.join(matched_points[:2])}"
        elif screening_result == 'REVIEW':
            return f"候选人基本符合要求，但需重点关注: {'; '.join(unmatched_points[:2])}，建议人工复核"
        else:
            return f"候选人与岗位要求差距较大，主要问题: {'; '.join(unmatched_points[:3])}，不建议面试"

    def auto_match_resume(
        self,
        resume: Dict,
        jobs: List[Dict],
        top_n: int = 2
    ) -> List[Dict]:
        """自动匹配简历与所有岗位，返回前N个最佳匹配

        Args:
            resume: 简历信息（解析后的）
            jobs: 所有岗位列表
            top_n: 返回前N个最佳匹配结果，默认2

        Returns:
            前N个最佳匹配结果列表，按匹配分数降序排序
        """
        results = []

        # 遍历所有岗位进行匹配
        for job in jobs:
            try:
                match_result = self.match(resume, job)

                # 组合结果
                combined_result = {
                    'job_id': job.get('id'),
                    'job_name': job.get('name'),
                    'job_category': job.get('category'),
                    'match_score': match_result['match_score'],
                    'skill_score': match_result['skill_score'],
                    'experience_score': match_result['experience_score'],
                    'education_score': match_result['education_score'],
                    'screening_result': match_result['screening_result'],
                    'matched_points': match_result['matched_points'],
                    'unmatched_points': match_result['unmatched_points'],
                    'suggestion': match_result['suggestion'],
                    'confidence': match_result['confidence']
                }

                results.append(combined_result)

            except Exception as e:
                logger.error(f"匹配岗位 {job.get('name')} 时出错: {str(e)}")
                continue

        # 按匹配分数降序排序
        results.sort(key=lambda x: x['match_score'], reverse=True)

        # 返回前N个最佳匹配
        top_results = results[:top_n]

        logger.info(
            f"简历 {resume.get('candidate_name', 'Unknown')} 与 {len(jobs)} 个岗位匹配完成，"
            f"返回前 {len(top_results)} 个最佳匹配"
        )

        return top_results


# 使用示例
if __name__ == '__main__':
    matcher = JobMatcher()

    # 测试简历
    resume = {
        'candidate_name': '张三',
        'phone': '13800138000',
        'email': 'zhangsan@example.com',
        'education': '本科',
        'work_years': 3,
        'skills': ['Python', 'FastAPI', 'React', 'MySQL', 'Docker']
    }

    # 测试岗位
    job = {
        'name': 'Python后端工程师',
        'category': 'software',
        'required_skills': ['Python', 'FastAPI'],
        'preferred_skills': ['MySQL', 'Redis', 'Docker'],
        'min_education': '本科',
        'min_work_years': 2
    }

    result = matcher.match(resume, job)
    print(f"匹配结果: {result}")
