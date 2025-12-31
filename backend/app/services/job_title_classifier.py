"""职位分类服务 - 从邮件和简历中自动判断职位类型"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter

from app.data.job_titles import (
    JOB_TITLES,
    get_job_config,
    get_all_job_names,
    get_compiled_patterns,
    is_valid_job
)

logger = logging.getLogger(__name__)


class JobTitleClassifier:
    """职位分类器 - 基于多策略的职位判断引擎"""

    # 职位关键词（用于快速定位）
    JOB_KEYWORDS = [
        '应聘', '申请', '期望', '求职意向', '投递', '应聘岗位',
        '岗位', '职位', '应聘职位', '申请职位'
    ]

    # 熟练度权重映射
    PROFICIENCY_WEIGHTS = {
        'expert': 1.0,       # 100%
        'proficient': 0.8,   # 80%
        'familiar': 0.6,     # 60%
        'mentioned': 0.4,    # 40%
    }

    def __init__(self):
        """初始化职位分类器"""
        self.job_names = get_all_job_names()
        logger.info(f"职位分类器初始化完成，支持 {len(self.job_names)} 个职位")

    def classify_job_title(
        self,
        email_subject: str = '',
        resume_text: str = '',
        skills: Optional[List[str]] = None,
        skills_by_level: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """按优先级判断职位

        优先级顺序:
        1. 从邮件标题提取（精确+模糊）
        2. 从简历内容提取（精确+模糊）
        3. 根据技能组合推断（必需+加分）

        Args:
            email_subject: 邮件主题
            resume_text: 简历文本内容
            skills: 技能列表（向后兼容）
            skills_by_level: 按熟练度分类的技能

        Returns:
            职位名称，如"Java开发"；无匹配返回"待分类"
        """
        if skills is None:
            skills = []
        if skills_by_level is None:
            skills_by_level = {}

        # 步骤1: 从邮件标题提取
        job_title = self._extract_from_subject(email_subject)
        if job_title:
            logger.info(f"从邮件标题提取到职位: {job_title}")
            return job_title

        # 步骤2: 从简历内容提取
        job_title = self._extract_from_resume(resume_text)
        if job_title:
            logger.info(f"从简历内容提取到职位: {job_title}")
            return job_title

        # 步骤3: 基于技能推断
        job_title = self._infer_from_skills(skills, skills_by_level)
        if job_title:
            logger.info(f"从技能推断出职位: {job_title}")
            return job_title

        logger.debug("未能从任何来源判断出职位，标记为待分类")
        return "待分类"

    def _extract_from_subject(self, subject: str) -> Optional[str]:
        """从邮件主题提取职位

        支持格式:
        - "应聘Java开发工程师" -> "Java开发"
        - "Java开发-张三" -> "Java开发"
        - "申请岗位：前端开发" -> "前端开发"

        策略:
        1. 优先匹配"应聘/申请/期望"后面的职位
        2. 匹配"职位-姓名"或"职位-城市"格式
        3. 全局搜索（只有一个职位时）

        Args:
            subject: 邮件主题

        Returns:
            职位名称，未找到返回None
        """
        if not subject:
            return None

        subject = subject.strip()

        # 策略1: 匹配"应聘/申请/期望"后面的职位
        for keyword in self.JOB_KEYWORDS:
            # 匹配 "关键词：职位" 或 "关键词职位" 或 "关键词-职位"
            patterns = [
                rf'{keyword}[:：\s\-]*(.+?)(?:[\-|/]|$)',  # 应聘:Java开发 或 应聘Java开发
            ]

            for pattern in patterns:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip()
                    # 尝试精确+模糊匹配
                    job_title = self._match_job_title(candidate)
                    if job_title:
                        return job_title

        # 策略2: 匹配"职位-XXX"格式（开头）
        # 例如: "Java开发-张三", "前端开发工程师-简历"
        pattern = r'^([^|/\-]{2,20}?开发|[^|/\-]{2,20}?工程|[^|/\-]{2,20}?经理|[^|/\-]{2,20}?总监|[^|/\-]{2,20}?专员|[^|/\-]{2,20}?顾问|[^|/\-]{2,20}?师)[\-|/]'
        match = re.search(pattern, subject)
        if match:
            candidate = match.group(1).strip()
            job_title = self._match_job_title(candidate)
            if job_title:
                return job_title

        # 策略3: 匹配"XXX-职位"格式（结尾）
        # 例如: "张三-Java开发", "简历-产品经理"
        pattern = r'[\-|/]([^|/\-]{2,20}?开发|[^|/\-]{2,20}?工程|[^|/\-]{2,20}?经理|[^|/\-]{2,20}?总监|[^|/\-]{2,20}?专员|[^|/\-]{2,20}?顾问|[^|/\-]{2,20}?师)$'
        match = re.search(pattern, subject)
        if match:
            candidate = match.group(1).strip()
            job_title = self._match_job_title(candidate)
            if job_title:
                return job_title

        # 策略4: 全局搜索（如果主题中只包含一个职位）
        matched_jobs = []
        for job_name in self.job_names:
            job_config = get_job_config(job_name)

            # 精确匹配
            if self._exact_match(subject, job_config):
                matched_jobs.append((job_name, job_config['priority'], 100))
                continue

            # 模糊匹配
            if self._fuzzy_match(subject, job_config):
                matched_jobs.append((job_name, job_config['priority'], 80))

        if len(matched_jobs) == 1:
            return matched_jobs[0][0]

        # 如果匹配多个，选择优先级最高的
        if len(matched_jobs) > 1:
            matched_jobs.sort(key=lambda x: (x[1], x[2]), reverse=True)
            return matched_jobs[0][0]

        return None

    def _extract_from_resume(self, text: str) -> Optional[str]:
        """从简历文本提取职位

        策略:
        1. 优先匹配"求职意向/期望岗位/应聘职位"等关键词
        2. 从工作经历中推断（最近的职位）
        3. 从自我评价/专业技能中推断

        Args:
            text: 简历文本

        Returns:
            职位名称，未找到返回None
        """
        if not text:
            return None

        # 只检查前8000个字符（通常求职意向在前半部分）
        text = text[:8000]

        # 策略1: 匹配"求职意向/期望岗位"等关键词
        intention_patterns = [
            r'求职意向[:：\s]*(.+?)(?:\n|$)',
            r'期望岗位[:：\s]*(.+?)(?:\n|$)',
            r'应聘职位[:：\s]*(.+?)(?:\n|$)',
            r'应聘岗位[:：\s]*(.+?)(?:\n|$)',
            r'意向职位[:：\s]*(.+?)(?:\n|$)',
            r'期望职位[:：\s]*(.+?)(?:\n|$)',
        ]

        for pattern in intention_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # 清理多余的字符
                candidate = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\-]', '', candidate)
                job_title = self._match_job_title(candidate)
                if job_title:
                    return job_title

        # 策略2: 从工作经历中提取（查找"最近/现任职位"）
        # 通常格式：2020-至今 | Java开发工程师 | XX公司
        work_patterns = [
            r'\d{4}.*?至今.*?[:：|](.+?)(?:[:：|])',
            r'\d{4}.*?现在.*?[:：|](.+?)(?:[:：|])',
            r'现任[:：\s]*(.+?)(?:\n|$)',
            r'最近职位[:：\s]*(.+?)(?:\n|$)',
        ]

        for pattern in work_patterns:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1).strip()
                job_title = self._match_job_title(candidate)
                if job_title:
                    return job_title

        # 策略3: 统计所有职位相关词的出现频率
        job_counts = Counter()

        for job_name in self.job_names:
            job_config = get_job_config(job_name)

            # 统计精确模式出现次数
            for pattern in job_config.get('exact_patterns', []):
                count = len(re.findall(re.escape(pattern), text))
                if count > 0:
                    job_counts[job_name] += count * 3  # 精确匹配权重高

            # 统计模糊模式出现次数
            compiled_patterns = get_compiled_patterns(job_name)
            for compiled_pattern in compiled_patterns:
                count = len(compiled_pattern.findall(text))
                if count > 0:
                    job_counts[job_name] += count  # 模糊匹配权重低

        # 如果有统计结果，选择出现次数最多的
        if job_counts:
            most_common = job_counts.most_common(1)[0]
            if most_common[1] >= 2:  # 至少出现2次
                return most_common[0]

        return None

    def _infer_from_skills(
        self,
        skills: List[str],
        skills_by_level: Dict[str, List[str]]
    ) -> Optional[str]:
        """基于技能推断职位

        策略:
        1. 检查每个职位的必需技能，必须至少匹配N%
        2. 计算加分技能匹配数
        3. 选择必需+加分综合得分最高的职位
        4. 考虑熟练度加权：expert > proficient > familiar > mentioned

        Args:
            skills: 技能列表（扁平）
            skills_by_level: 按熟练度分类的技能

        Returns:
            职位名称，未找到返回None
        """
        # 创建简历技能集合（所有级别）
        all_resume_skills = set(skills)
        for level_skills in skills_by_level.values():
            all_resume_skills.update(level_skills)

        if not all_resume_skills:
            return None

        # 标准化为小写用于比较
        resume_skills_lower = {s.lower(): s for s in all_resume_skills}

        job_scores = []

        for job_name in self.job_names:
            job_config = get_job_config(job_name)

            # 计算必需技能得分
            required_score, required_details = self._calculate_required_skill_score(
                job_config.get('required_skills', []),
                all_resume_skills,
                skills_by_level,
                job_config.get('required_ratio', 0.5)
            )

            # 如果不满足必需技能最低要求，跳过
            if not required_details['meets_threshold']:
                continue

            # 计算加分技能得分
            bonus_score = self._calculate_bonus_skill_score(
                job_config.get('bonus_skills', []),
                all_resume_skills,
                skills_by_level
            )

            # 综合得分 = 必需技能得分 * 0.6 + 加分技能得分 * 0.4
            total_score = required_score * 0.6 + bonus_score * 0.4

            job_scores.append({
                'job_name': job_name,
                'total_score': total_score,
                'required_score': required_score,
                'bonus_score': bonus_score,
                'priority': job_config.get('priority', 50)
            })

        # 如果没有匹配的职位
        if not job_scores:
            return None

        # 按总分和优先级排序
        # 先按优先级降序，再按分数降序
        job_scores.sort(key=lambda x: (x['priority'], x['total_score']), reverse=True)

        # 返回最佳匹配
        best_match = job_scores[0]

        # 如果得分太低（<30），认为不够明确
        if best_match['total_score'] < 30:
            logger.debug(
                f"技能推断最佳匹配得分过低: {best_match['job_name']} "
                f"({best_match['total_score']:.1f}分)，不采用"
            )
            return None

        return best_match['job_name']

    def _calculate_required_skill_score(
        self,
        required_skills: List[str],
        resume_skills: set,
        skills_by_level: Dict[str, List[str]],
        required_ratio: float
    ) -> Tuple[float, Dict]:
        """计算必需技能得分

        Args:
            required_skills: 必需技能列表
            resume_skills: 简历技能集合
            skills_by_level: 按熟练度分类的技能
            required_ratio: 必需技能最低匹配比例

        Returns:
            (分数, 详细信息)
        """
        if not required_skills:
            return 100.0, {'meets_threshold': True, 'matched': [], 'total': 0}

        matched_scores = []
        matched_skills = []

        for skill in required_skills:
            skill_lower = skill.lower()

            # 检查是否在简历中
            found = False
            proficiency = None

            # 优先从skills_by_level查找（带熟练度）
            if skills_by_level:
                for level, level_skills in skills_by_level.items():
                    for resume_skill in level_skills:
                        if resume_skill.lower() == skill_lower:
                            found = True
                            proficiency = level
                            break
                    if found:
                        break

            # 向后兼容：从扁平技能列表查找
            if not found and skill_lower in [s.lower() for s in resume_skills]:
                found = True
                proficiency = 'proficient'  # 默认熟练度

            if found:
                # 根据熟练度计算分数
                weight = self.PROFICIENCY_WEIGHTS.get(proficiency, 0.7)
                matched_scores.append(100 * weight)
                matched_skills.append(f"{skill} ({proficiency})")

        # 计算平均分
        if matched_scores:
            avg_score = sum(matched_scores) / len(required_skills)
        else:
            avg_score = 0.0

        # 检查是否满足最低匹配比例
        match_ratio = len(matched_scores) / len(required_skills)
        meets_threshold = match_ratio >= required_ratio

        details = {
            'meets_threshold': meets_threshold,
            'matched': matched_skills,
            'total': len(required_skills),
            'matched_count': len(matched_scores),
            'match_ratio': match_ratio
        }

        return avg_score, details

    def _calculate_bonus_skill_score(
        self,
        bonus_skills: List[str],
        resume_skills: set,
        skills_by_level: Dict[str, List[str]]
    ) -> float:
        """计算加分技能得分

        Args:
            bonus_skills: 加分技能列表
            resume_skills: 简历技能集合
            skills_by_level: 按熟练度分类的技能

        Returns:
            分数 (0-100)
        """
        if not bonus_skills:
            return 0.0

        matched_scores = []

        for skill in bonus_skills:
            skill_lower = skill.lower()

            # 检查是否在简历中
            found = False
            proficiency = None

            if skills_by_level:
                for level, level_skills in skills_by_level.items():
                    for resume_skill in level_skills:
                        if resume_skill.lower() == skill_lower:
                            found = True
                            proficiency = level
                            break
                    if found:
                        break

            if not found and skill_lower in [s.lower() for s in resume_skills]:
                found = True
                proficiency = 'proficient'

            if found:
                weight = self.PROFICIENCY_WEIGHTS.get(proficiency, 0.7)
                matched_scores.append(100 * weight)

        # 计算得分：匹配数 / 总数 * 100
        if matched_scores:
            # 考虑熟练度的加权平均
            avg_score = sum(matched_scores) / len(bonus_skills)
        else:
            avg_score = 0.0

        return avg_score

    def _match_job_title(self, candidate: str) -> Optional[str]:
        """尝试将候选文本匹配到职位名称

        先精确匹配，再模糊匹配

        Args:
            candidate: 候选职位文本

        Returns:
            匹配的职位名称，未找到返回None
        """
        if not candidate:
            return None

        # 收集所有匹配的职位
        matched_jobs = []

        for job_name in self.job_names:
            job_config = get_job_config(job_name)

            # 精确匹配
            if self._exact_match(candidate, job_config):
                matched_jobs.append((job_name, job_config['priority'], 100))
                continue

            # 模糊匹配
            if self._fuzzy_match(candidate, job_config):
                matched_jobs.append((job_name, job_config['priority'], 80))

        if not matched_jobs:
            return None

        # 按优先级和分数排序
        matched_jobs.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return matched_jobs[0][0]

    def _exact_match(self, text: str, job_config: Dict) -> bool:
        """精确匹配职位名称

        Args:
            text: 要匹配的文本
            job_config: 职位配置

        Returns:
            是否匹配
        """
        exact_patterns = job_config.get('exact_patterns', [])

        for pattern in exact_patterns:
            # 使用完整单词匹配，避免部分匹配
            if pattern in text:
                return True

        return False

    def _fuzzy_match(self, text: str, job_config: Dict) -> bool:
        """模糊匹配职位名称（使用预编译正则表达式）

        Args:
            text: 要匹配的文本
            job_config: 职位配置

        Returns:
            是否匹配
        """
        job_name = job_config.get('name', '')
        if not job_name:
            return False

        compiled_patterns = get_compiled_patterns(job_name)

        for pattern in compiled_patterns:
            if pattern.search(text):
                return True

        return False
