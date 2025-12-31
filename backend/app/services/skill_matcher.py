"""高级技能匹配器 - 语义理解和关联匹配"""
from typing import Dict, List, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class SemanticSkillMatcher:
    """语义技能匹配器 - 处理技能层级关系和相似度"""

    def __init__(self):
        """初始化语义匹配器"""
        self.skill_hierarchy = self._build_skill_hierarchy()
        self.skill_similarities = self._build_skill_similarities()

    def _build_skill_hierarchy(self) -> Dict[str, List[str]]:
        """构建技能层级关系 (父 -> 子)

        用于处理：
        - "熟悉Spring框架" 可以匹配 "Spring Boot" 要求
        - "SQL" 可以匹配 "MySQL/PostgreSQL" 要求
        """
        return {
            # Spring 生态系统
            'Spring': ['Spring Boot', 'Spring MVC', 'Spring Cloud', 'Spring Data'],
            'Spring Framework': ['Spring Boot', 'Spring MVC', 'Spring Cloud', 'Spring Data'],

            # React 生态系统
            'React': ['React Native', 'Next.js', 'Redux', 'React Query'],

            # 数据库分类
            'SQL': ['MySQL', 'PostgreSQL', 'SQL Server', 'Oracle', 'SQLite'],
            'NoSQL': ['MongoDB', 'Redis', 'Cassandra', 'DynamoDB', 'Elasticsearch'],
            'Relational Database': ['MySQL', 'PostgreSQL', 'SQL Server', 'Oracle', 'SQLite'],

            # 云平台分类
            'Cloud': ['AWS', 'Azure', 'GCP', '阿里云', '腾讯云', '华为云'],
            'Cloud Computing': ['AWS', 'Azure', 'GCP', '阿里云', '腾讯云'],

            # AI/ML 分类
            'Deep Learning': ['TensorFlow', 'PyTorch', 'Keras', 'Caffe'],
            'Machine Learning': ['TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost', 'LightGBM'],
            'Data Science': ['Pandas', 'NumPy', 'Jupyter', 'Matplotlib', 'Scikit-learn'],

            # 前端分类
            'Frontend': ['React', 'Vue', 'Angular', 'JavaScript', 'TypeScript', 'HTML', 'CSS'],
            'Backend': ['Python', 'Java', 'Go', 'Node.js', 'C#', 'PHP'],
            'Full Stack': ['React', 'Vue', 'Python', 'Java', 'JavaScript', 'TypeScript'],

            # DevOps 分类
            'Container': ['Docker', 'Kubernetes', 'Podman'],
            'Orchestration': ['Kubernetes', 'Docker Swarm', 'Mesos'],
            'CI/CD': ['Jenkins', 'GitHub Actions', 'GitLab CI', 'Travis CI', 'CircleCI'],

            # 大数据分类
            'Data Processing': ['Spark', 'Flink', 'Hadoop', 'Kafka'],
            'Data Storage': ['Hadoop', 'HBase', 'Cassandra', 'MongoDB', 'Elasticsearch'],

            # 移动开发分类
            'Mobile Development': ['iOS', 'Android', 'React Native', 'Flutter'],
            'iOS Development': ['Swift', 'SwiftUI', 'Objective-C'],
            'Android Development': ['Kotlin', 'Java', 'Jetpack Compose'],
        }

    def _build_skill_similarities(self) -> Dict[str, List[str]]:
        """构建技能相似度映射

        用于处理相关但层级不明确的技能
        """
        return {
            # 编程语言相关
            'Python': ['Django', 'Flask', 'FastAPI', 'PyTorch', 'TensorFlow', 'Pandas', 'NumPy'],
            'JavaScript': ['React', 'Vue', 'Angular', 'Node.js', 'TypeScript', 'jQuery', 'Express'],
            'Java': ['Spring', 'Spring Boot', 'Maven', 'Gradle', 'Jakarta EE'],
            'Go': ['Golang', 'Gin', 'Echo', 'gRPC'],
            'C#': ['.NET', 'ASP.NET', 'Entity Framework', 'LINQ'],

            # 前端相关
            'Frontend': ['HTML', 'CSS', 'JavaScript', 'TypeScript', 'React', 'Vue', 'Angular'],
            'Backend': ['Python', 'Java', 'Go', 'Node.js', 'C#', 'PHP', 'Ruby'],

            # 数据相关
            'Database': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQL Server'],
            'Data Analysis': ['Pandas', 'NumPy', 'Excel', 'SQL', 'Matplotlib', 'Tableau'],

            # DevOps 相关
            'DevOps': ['Docker', 'Kubernetes', 'Jenkins', 'Git', 'CI/CD', 'Linux', 'Terraform'],
            'Monitoring': ['Prometheus', 'Grafana', 'ELK', 'Splunk', 'Datadog', 'New Relic'],

            # 云平台相关
            'AWS': ['EC2', 'S3', 'Lambda', 'RDS', 'DynamoDB', 'EKS', 'ECS'],
            'Azure': ['Blob Storage', 'Cosmos DB', 'Azure Functions', 'AKS'],
            'GCP': ['BigQuery', 'Cloud Functions', 'Compute Engine'],

            # 大数据相关
            'Big Data': ['Hadoop', 'Spark', 'Flink', 'Kafka', 'Hive', 'HBase'],
            'Data Engineering': ['Spark', 'Kafka', 'Airflow', 'Hadoop', 'Flink'],

            # AI/ML 相关
            'AI': ['TensorFlow', 'PyTorch', 'Scikit-learn', 'Keras', 'Machine Learning', 'Deep Learning'],
            'ML': ['TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost', 'LightGBM', 'Pandas', 'NumPy'],
            'Data Science': ['Pandas', 'NumPy', 'Matplotlib', 'Scikit-learn', 'Jupyter'],
        }

    def find_semantic_matches(
        self,
        required_skills: List[str],
        resume_skills: List[str],
        skills_by_level: Dict[str, List[str]]
    ) -> Tuple[List[str], Dict[str, float]]:
        """查找语义匹配

        Args:
            required_skills: 岗位要求的技能列表
            resume_skills: 简历中的技能列表（用于向后兼容）
            skills_by_level: 按熟练度分类的技能

        Returns:
            (matched_skills, match_scores)
            - matched_skills: 匹配到的技能列表（可能包含 "skill (related)" 格式）
            - match_scores: 每个技能的匹配分数 (0.0-1.0)
        """
        import re

        # 创建简历技能集合（所有级别）
        all_resume_skills = set()
        for level_skills in skills_by_level.values():
            all_resume_skills.update(level_skills)
        all_resume_skills.update(resume_skills)

        # 标准化为小写用于比较
        resume_skills_lower = {s.lower(): s for s in all_resume_skills}

        matched = []
        scores = {}

        for required in required_skills:
            required_lower = required.lower()

            # 1. 检查精确匹配
            if required_lower in resume_skills_lower:
                matched.append(required)
                scores[required] = 1.0
                continue

            # 2. 检查层级匹配（子技能匹配父技能）
            for parent, children in self.skill_hierarchy.items():
                if required in children:
                    # 检查父技能是否在简历中
                    if parent.lower() in resume_skills_lower:
                        matched.append(f"{required} (via {parent})")
                        scores[required] = 0.8
                        break
                    # 检查兄弟技能是否在简历中（表明了解这个家族）
                    elif any(child.lower() in resume_skills_lower for child in children):
                        matched.append(f"{required} (related)")
                        scores[required] = 0.7
                        break

            # 3. 如果还没匹配到，检查相似度映射
            if required not in scores:
                for skill, similars in self.skill_similarities.items():
                    if required_lower == skill.lower():
                        # 检查是否有相似技能
                        for similar in similars:
                            if similar.lower() in resume_skills_lower:
                                matched.append(f"{required} (similar to {similar})")
                                scores[required] = 0.6
                                break
                        break

            # 4. 部分匹配（技能名称包含关系）
            if required not in scores:
                for resume_skill in all_resume_skills:
                    # 检查是否包含相同的词根
                    if self._has_common_word_root(required, resume_skill):
                        confidence = self._calculate_partial_match_confidence(required, resume_skill)
                        if confidence >= 0.5:
                            matched.append(f"{required} (partial match to {resume_skill})")
                            scores[required] = confidence
                            break

        return matched, scores

    def _has_common_word_root(self, skill1: str, skill2: str) -> bool:
        """检查两个技能是否有共同的词根"""
        # 简单的词根检查
        words1 = set(skill1.lower().split())
        words2 = set(skill2.lower().split())

        # 检查是否有任何共同的词
        return bool(words1 & words2)

    def _calculate_partial_match_confidence(self, required: str, resume_skill: str) -> float:
        """计算部分匹配的置信度

        规则：
        - 包含完整技能名：0.9
        - 包含主要关键词：0.7
        - 有共同词根：0.5
        """
        required_lower = required.lower()
        resume_lower = resume_skill.lower()

        # 完全包含
        if required_lower in resume_lower or resume_lower in required_lower:
            return 0.9

        # 提取主要关键词（去除常见词）
        common_words = {'development', 'programming', 'language', 'framework', 'tool'}
        words1 = set(required_lower.split()) - common_words
        words2 = set(resume_lower.split()) - common_words

        if words1 & words2:
            # 有共同的主要关键词
            overlap_ratio = len(words1 & words2) / max(len(words1), len(words2))
            return 0.5 + overlap_ratio * 0.3

        return 0.0
