"""学校分类服务 - 判断985/211/QS排名

综合判断中国大学（985/211）和国外大学（QS排名）
"""

import logging
from typing import Optional

from app.data.chinese_universities import get_school_type
from app.data.foreign_universities import get_qs_ranking

logger = logging.getLogger(__name__)


class SchoolClassifier:
    """学校分类器 - 判断学校类型"""

    def __init__(self):
        """初始化学校分类器"""
        logger.info("学校分类器初始化完成")

    def classify(self, school_name: str) -> Optional[str]:
        """
        判断学校类型

        优先级：
        1. QS排名（国外大学优先）
        2. 中国985/211

        Args:
            school_name: 学校名称

        Returns:
            学校类型标注：985/211/双非/QS前50/QS前100
            无法识别返回None
        """
        if not school_name:
            return None

        # 清理学校名称（去除空格和特殊字符）
        school_name = school_name.strip()

        # 先判断是否为国外大学（QS排名）
        qs_ranking = get_qs_ranking(school_name)
        if qs_ranking:
            logger.debug(f"学校 '{school_name}' 识别为国外大学：{qs_ranking}")
            return qs_ranking

        # 判断中国大学（985/211/双非）
        school_type = get_school_type(school_name)
        if school_type:
            logger.debug(f"学校 '{school_name}' 识别为中国大学：{school_type}")
            return school_type

        # 无法识别
        logger.debug(f"无法识别学校类型：'{school_name}'")
        return None

    def classify_batch(self, school_names: list) -> dict:
        """
        批量判断学校类型

        Args:
            school_names: 学校名称列表

        Returns:
            学校类型映射字典 {school_name: school_type}
        """
        results = {}
        for school_name in school_names:
            results[school_name] = self.classify(school_name)
        return results


# 全局单例
_classifier_instance = None


def get_school_classifier() -> SchoolClassifier:
    """获取学校分类器单例"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SchoolClassifier()
    return _classifier_instance
