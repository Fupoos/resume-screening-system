"""项目经历提取器 - 从简历文本中提取项目经历信息"""
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ProjectExtractor:
    """项目经历提取器

    从简历文本中提取项目经历信息，包括：
    - 项目名称
    - 项目角色
    - 项目时间
    - 项目描述
    - 技术栈
    """

    @staticmethod
    def extract_project_experience(text: str) -> List[Dict]:
        """提取项目经历"""
        project_list = []

        # 项目经历关键词
        keywords = ['项目经历', '项目经验', '项目']

        # 查找项目经历段落
        lines = text.split('\n')
        start_idx = None

        for i, line in enumerate(lines):
            if any(keyword in line for keyword in keywords):
                start_idx = i
                break

        if start_idx is None:
            return project_list

        # 解析项目经历（简单实现）
        for i in range(start_idx + 1, min(start_idx + 30, len(lines))):
            line = lines[i].strip()

            if not line:
                continue

            # 检查是否是项目名称（简单判断）
            if len(line) < 50 and '项目' in line:
                project = {
                    'name': line,
                    'role': '',
                    'duration': '',
                    'description': '',
                    'tech_stack': []
                }
                project_list.append(project)

                if len(project_list) >= 5:  # 最多取5条
                    break

        return project_list
