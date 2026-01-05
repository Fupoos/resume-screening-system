"""大学分类服务

从简历文本中提取学校名称并分类为985/211/QS前50/100/200/双非
"""
import re
from typing import Optional, List
from app.data.university_database import classify_university

# 常见大学名称模式
UNIVERSITY_PATTERNS = [
    # 中国大学常见模式
    r'([^，。,\.\s]{2,8})(大学|学院)',
    # 港澳台大学
    r'([^，。,\.\s]{2,10})(大学|學院)',
    # 国外大学
    r'(University|Institute|College|School)\s+of\s+([^，。,\.\s]{2,20})',
    r'([^，。,\.\s]{2,20})(University|Institute|College|School)',
]

# 学历背景关键词
EDUCATION_KEYWORDS = [
    '教育背景', '学历', '教育经历', '教育', '学习经历',
    '本科', '硕士', '博士', '研究生', '学士',
    '毕业院校', '毕业于', '就读于',
]


def extract_school_from_text(text: str) -> Optional[str]:
    """从简历文本中提取最高学历的学校名称

    Args:
        text: 简历原始文本

    Returns:
        学校名称或None
    """
    if not text:
        return None

    # 1. 定位教育背景部分（通常在简历前半部分）
    education_section = None
    for keyword in EDUCATION_KEYWORDS:
        # 查找关键词位置
        idx = text.find(keyword)
        if idx != -1:
            # 从关键词开始，取接下来的2000字符（教育背景通常不会太长）
            section_start = idx
            section_end = min(idx + 2000, len(text))
            education_section = text[section_start:section_end]
            break

    # 如果没找到教育背景部分，使用前3000字符
    if not education_section:
        education_section = text[:3000]

    # 2. 在教育背景部分提取学校名称
    schools_found = []

    # 使用正则模式匹配
    for pattern in UNIVERSITY_PATTERNS:
        matches = re.finditer(pattern, education_section)
        for match in matches:
            if match.group(1):
                school_name = match.group(1).strip()
                # 过滤掉明显不是学校的词
                if not is_invalid_school_name(school_name):
                    schools_found.append(school_name)

    # 3. 去重并返回第一个找到的学校
    if schools_found:
        # 使用第一个找到的学校（通常是最高学历）
        unique_schools = list(dict.fromkeys(schools_found))  # 保持顺序的去重
        return unique_schools[0]

    return None


def is_invalid_school_name(name: str) -> bool:
    """检查是否为无效的学校名称

    Args:
        name: 学校名称

    Returns:
        True表示无效，False表示可能有效
    """
    if not name:
        return True

    # 排除明显不是学校的词
    invalid_keywords = [
        '技术', '工程', '科学', '文学', '经济', '管理', '法律',
        '计算机', '软件', '电子', '机械', '建筑', '艺术', '医学',
        '专业', '课程', '主修', '辅修', '方向', '系', '所',
        '在职', '全日制', '业余', '函授', '自考',
        '时间', '年', '月', '至', '起止',
        '高中', '初中', '小学', '中学',
    ]

    for keyword in invalid_keywords:
        if name == keyword or name in keyword:
            return True

    # 长度检查
    if len(name) < 2 or len(name) > 15:
        return True

    return False


def classify_education_level(text: str) -> Optional[str]:
    """从简历文本中分类学历等级

    Args:
        text: 简历原始文本

    Returns:
        学历等级：'985', '211', 'QS前50', 'QS前100', 'QS前200', '双非' 或 None
    """
    # 提取学校名称
    school_name = extract_school_from_text(text)

    if not school_name:
        return None

    # 分类学校等级
    level = classify_university(school_name)

    return level


def batch_classify_education_levels(raw_texts: List[str]) -> List[Optional[str]]:
    """批量分类学历等级

    Args:
        raw_texts: 简历原始文本列表

    Returns:
        学历等级列表
    """
    results = []
    for text in raw_texts:
        level = classify_education_level(text)
        results.append(level)
    return results
