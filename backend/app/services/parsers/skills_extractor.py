"""技能提取器 - 从简历文本中提取技能信息"""
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SkillsExtractor:
    """技能提取器

    从简历文本中提取技能信息，包括：
    - 技能名称列表
    - 技能熟练度分类（精通、熟悉、了解、提及）
    """

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """提取技能关键词 - 改进版"""
        from app.data.skills_database import SKILLS_DATABASE, SKILL_SYNONYMS

        skills_found = set()
        text_lower = text.lower()

        # 1. 遍历所有技能分类
        for category, skills in SKILLS_DATABASE.items():
            for skill in skills:
                # 2. 精确匹配（支持中英文混合环境的边界检测）
                # 使用负向环视替代 \b，因为 \b 对中文字符无效
                # 只排除ASCII字母数字，允许中文和其他字符
                # (?<![a-zA-Z0-9]) - 前面不是ASCII字母/数字
                # (?![a-zA-Z0-9]) - 后面不是ASCII字母/数字
                pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
                if re.search(pattern, text_lower):
                    # 3. 如果是同义词，映射到标准名称
                    standardized_skill = SKILL_SYNONYMS.get(skill.lower(), skill)
                    skills_found.add(standardized_skill)

        # 4. 按优先级排序（编程语言 > 框架 > 工具）
        skill_priority = {
            'Python': 10, 'Java': 10, 'JavaScript': 10, 'TypeScript': 10, 'Go': 10, 'C++': 10,
            'React': 9, 'Vue': 9, 'Angular': 9, 'Django': 9, 'Flask': 9, 'FastAPI': 9, 'Node.js': 9,
            'MySQL': 8, 'PostgreSQL': 8, 'MongoDB': 8, 'Redis': 8, 'Oracle': 8,
            'Docker': 8, 'Kubernetes': 8, 'Linux': 8, 'Git': 8, 'Jenkins': 8,
            'Excel': 7, 'SAP': 7, 'Word': 7, 'PowerPoint': 7,
            '财务': 6, '会计': 6, '审计': 6, '税务': 6,
            '招聘': 5, '培训': 5, '绩效管理': 5, '项目管理': 5,
        }

        # 5. 转为列表并排序
        skills_list = list(skills_found)
        skills_list.sort(key=lambda x: skill_priority.get(x, 0), reverse=True)

        # 6. 限制最多返回20个技能
        return skills_list[:20]

    @staticmethod
    def extract_skills_with_proficiency(text: str) -> Dict[str, List[str]]:
        """提取技能并识别熟练程度

        返回:
        {
            'expert': ['Python', 'Java'],      # 精通
            'proficient': ['JavaScript'],      # 熟悉
            'familiar': ['Rust'],              # 了解
            'mentioned': ['Excel'],            # 仅提及
        }
        """
        from app.data.skills_database import SKILLS_DATABASE, SKILL_SYNONYMS
        import re
        from typing import Dict, List

        # 熟练度关键词模式
        PROFICIENCY_PATTERNS = {
            'expert': [
                r'精通[，、,\s]*([^，,。\s]{2,15})',
                r'熟练掌握[，、,\s]*([^，,。\s]{2,15})',
                r'擅长[，、,\s]*([^，,。\s]{2,15})',
            ],
            'proficient': [
                r'熟悉[，、,\s]*([^，,。\s]{2,15})',
                r'掌握[，、,\s]*([^，,。\s]{2,15})',
            ],
            'familiar': [
                r'了解[，、,\s]*([^，,。\s]{2,15})',
                r'接触过[，、,\s]*([^，,。\s]{2,15})',
            ]
        }

        skills_by_level = {
            'expert': [],
            'proficient': [],
            'familiar': [],
            'mentioned': []
        }
        skills_with_proficiency = set()

        # 提取带熟练度标记的技能
        for level, patterns in PROFICIENCY_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    skill_text = match.group(1).strip()
                    # 从文本中提取技能名称（处理"熟悉Python、Java"情况）
                    extracted = SkillsExtractor._extract_skill_names(skill_text)
                    for skill in extracted:
                        # 标准化技能名称
                        standardized = SKILL_SYNONYMS.get(skill.lower(), skill)
                        skills_by_level[level].append(standardized)
                        skills_with_proficiency.add(standardized)

        # 提取所有技能（用于无熟练度标记的）
        all_skills = SkillsExtractor.extract_skills(text)
        for skill in all_skills:
            standardized = SKILL_SYNONYMS.get(skill.lower(), skill)
            if standardized not in skills_with_proficiency:
                skills_by_level['mentioned'].append(standardized)

        # 去重
        for level in skills_by_level:
            skills_by_level[level] = list(set(skills_by_level[level]))

        return skills_by_level

    @staticmethod
    def _extract_skill_names(text: str) -> List[str]:
        """从文本中提取技能名称

        e.g., "Python、Java、Go" -> ['Python', 'Java', 'Go']
        """
        from app.data.skills_database import SKILLS_DATABASE
        import re

        found_skills = []

        # 尝试直接匹配已知技能
        for category, skills in SKILLS_DATABASE.items():
            for skill in skills:
                pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
                if re.search(pattern, text.lower()):
                    found_skills.append(skill)

        return found_skills
