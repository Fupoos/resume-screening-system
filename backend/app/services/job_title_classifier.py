"""职位分类服务 - 从邮件和简历中提取职位名称（仅字符串匹配）

根据CLAUDE.md核心原则：
- 只使用简单的字符串匹配提取职位名称
- 不包含任何技能推��、评分逻辑
- 所有评分由外部Agent完成
"""
import re
import logging
from typing import Dict, List, Optional

from app.data.job_titles_minimal import (
    JOB_TITLES,
    get_job_config,
    get_all_job_names,
    get_compiled_patterns,
    is_valid_job
)

logger = logging.getLogger(__name__)


class JobTitleClassifier:
    """职位分类器 - 仅使用字符串匹配，不进行评分判断"""

    # 职位关键词（用于快速定位）
    JOB_KEYWORDS = [
        '应聘', '申请', '期望', '求职意向', '投递', '应聘岗位',
        '岗位', '职位', '应聘职位', '申请职位'
    ]

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
        """按优先级判断职位（仅使用字符串匹配，不评分）

        优先级顺序:
        1. 从邮件标题提取（精确+模糊）
        2. 从简历内容提取（关键词匹配）
        3. 无法判断 → 返回"待分类"

        ❌ 不再使用技能推断

        Args:
            email_subject: 邮件主题
            resume_text: 简历文本内容
            skills: 忽略（保留参数以向后兼容）
            skills_by_level: 忽略（保留参数以向后兼容）

        Returns:
            职位名称，如"Java开发"；无匹配返回"待分类"
        """
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

        # 步骤3: 无法判断
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
        pattern = r'^([^\-|/]{2,20}?开发|[^\-|/]{2,20}?工程|[^\-|/]{2,20}?经理|[^\-|/]{2,20}?总监|[^\-|/]{2,20}?专员|[^\-|/]{2,20}?顾问|[^\-|/]{2,20}?师)[\-|/]'
        match = re.search(pattern, subject)
        if match:
            candidate = match.group(1).strip()
            job_title = self._match_job_title(candidate)
            if job_title:
                return job_title

        # 策略3: 匹配"XXX-职位"格式（结尾）
        # 例如: "张三-Java开发", "简历-产品经理"
        pattern = r'[\-|/]([^\-|/]{2,20}?开发|[^\-|/]{2,20}?工程|[^\-|/]{2,20}?经理|[^\-|/]{2,20}?总监|[^\-|/]{2,20}?专员|[^\-|/]{2,20}?顾问|[^\-|/]{2,20}?师)$'
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
            compiled_patterns = get_compiled_patterns(job_name)

            # 使用预编译的模式进行匹配
            for compiled_pattern in compiled_patterns:
                if compiled_pattern.search(subject):
                    matched_jobs.append((job_name, job_config.get('priority', 50), 100))
                    break

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
            # 🔴 新增：匹配"工作经验 | 职位"格式（如"5年工作经验 | 项目经理/主管"）
            r'\d+年工作经验\s*\|\s*(.+?)(?:\s*\||\s*$)',
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
        job_counts = {}

        for job_name in self.job_names:
            compiled_patterns = get_compiled_patterns(job_name)
            for compiled_pattern in compiled_patterns:
                count = len(compiled_pattern.findall(text))
                if count > 0:
                    job_counts[job_name] = job_counts.get(job_name, 0) + count

        # 如果有统计结果，选择出现次数最多的
        if job_counts:
            most_common = max(job_counts.items(), key=lambda x: x[1])
            if most_common[1] >= 2:  # 至少出现2次
                return most_common[0]

        return None

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
            compiled_patterns = get_compiled_patterns(job_name)

            # 使用预编译模式进行匹配
            for compiled_pattern in compiled_patterns:
                if compiled_pattern.search(candidate):
                    matched_jobs.append((job_name, get_job_config(job_name).get('priority', 50), 100))
                    break

        if not matched_jobs:
            return None

        # 按优先级和分数排序
        matched_jobs.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return matched_jobs[0][0]
