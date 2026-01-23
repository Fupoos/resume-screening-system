"""城市提取服务 - 从邮件主题、正文、简历中提取城市信息"""
import re
import logging
from typing import Optional, List
from dataclasses import dataclass, field
from app.data.cities import ALL_CITIES, CITY_ALIASES, get_standard_city_name

logger = logging.getLogger(__name__)


@dataclass
class CityExtractionResult:
    """城市提取结果

    Attributes:
        confirmed_city: 确认城市（100%置信度，来自明确格式）
        candidate_cities: 候选城市列表（从统计、工作经历推断）
    """
    confirmed_city: Optional[str] = None
    candidate_cities: List[str] = field(default_factory=list)


class CityExtractor:
    """城市提取器"""

    def __init__(self):
        """初始化城市提取器"""
        # 构建城市正则表达式模式（按长度降序，避免短词匹配长词的一部分）
        sorted_cities = sorted(ALL_CITIES, key=len, reverse=True)
        city_pattern = '|'.join(re.escape(city) for city in sorted_cities)

        # 构建别名正则表达式模式
        alias_pattern = '|'.join(re.escape(alias) for alias in CITY_ALIASES.keys())

        # 组合模式：优先匹配完整城市名，再匹配别名
        self.city_pattern = f'({city_pattern}|{alias_pattern})'

        # 应聘关键词模式（用于从邮件主题提取）
        self.application_keywords = ['应聘', '申请', '期望', '求职意向', '投递', '岗位地点', '工作地点']

        logger.info(f"城市提取器初始化完成，支持 {len(ALL_CITIES)} 个城市，{len(CITY_ALIASES)}个别名")

    def extract_city(self, email_subject: str = '', email_body: str = '',
                     resume_text: str = '') -> CityExtractionResult:
        """按优先级提取城市，返回确认城市和候选城市

        只从邮件主题提取，不从正文和简历提取

        Args:
            email_subject: 邮件主题
            email_body: 邮件正文（不再使用）
            resume_text: 简历文本（不再使用）

        Returns:
            CityExtractionResult: 包含确认城市和候选城市列表
        """
        result = CityExtractionResult()

        # 只从邮件主题提取城市
        subject_result = self._extract_from_subject(email_subject)
        if subject_result.confirmed_city:
            result.confirmed_city = subject_result.confirmed_city
            logger.info(f"从邮件主题提取到确认城市: {result.confirmed_city}")

        # 不再提取候选城市
        result.candidate_cities = []

        return result

    # ========== 保留旧接口以保持兼容性 ==========
    def extract_city_simple(self, email_subject: str = '', email_body: str = '',
                           resume_text: str = '') -> Optional[str]:
        """简化版提取方法（保持向后兼容）

        只返回确认城市，不返回候选城市
        """
        result = self.extract_city(email_subject, email_body, resume_text)
        return result.confirmed_city

    # ========== 以下是私有方法 ==========

    def _extract_from_subject(self, subject: str) -> CityExtractionResult:
        """从邮件主题提取城市（区分确认和候选）

        确认城市来源：
        - BOSS直聘格式
        - 括号格式
        - 应聘/期望关键词格式
        - 城市-岗位 格式

        候选城市来源：
        - 主题中所有出现的城市（非确认城市）
        """
        result = CityExtractionResult()

        if not subject:
            return result

        subject = subject.strip()

        # ========== 确认城市提取 ==========

        # 格式1: BOSS直聘 【职位_城市_薪资】
        boss_pattern1 = r'【[^_]+_({0})_[^】]+】'.format(self.city_pattern)
        match = re.search(boss_pattern1, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                result.confirmed_city = standard_name
                logger.info(f"从BOSS格式提取到城市: {standard_name}")
                # 同时收集候选城市
                result.candidate_cities = []  # 只保留确认城市，不收集候选城市
                return result

        # 格式2: BOSS直聘 【职位（城市）_城市_薪资】
        boss_pattern2 = r'【[^（（]+\((({0}))\)[^】]+】'.format(self.city_pattern)
        match = re.search(boss_pattern2, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                result.confirmed_city = standard_name
                logger.info(f"从BOSS格式（括号内）提取到城市: {standard_name}")
                result.candidate_cities = []  # 只保留确认城市，不收集候选城市
                return result

        # 格式3: 括号城市标记 【城市】或[城市]
        bracket_city_pattern = r'[【\[]({0})[】\]]'.format(self.city_pattern)
        match = re.search(bracket_city_pattern, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                result.confirmed_city = standard_name
                logger.info(f"从括号格式提取到城市: {standard_name}")
                result.candidate_cities = []  # 只保留确认城市，不收集候选城市
                return result

        # 格式4: 应聘/期望关键词格式
        for keyword in self.application_keywords:
            patterns = [
                rf'{keyword}[:：\s\-]*({self.city_pattern})',
                rf'({self.city_pattern})[:：\s\-]*{keyword}',
            ]
            for pattern in patterns:
                match = re.search(pattern, subject)
                if match:
                    # get_standard_city_name 现在可以处理 tuple（来自嵌套捕获组）
                    city_name = match.group(1)
                    standard_name = get_standard_city_name(city_name)
                    if standard_name:
                        result.confirmed_city = standard_name
                        result.candidate_cities = []  # 只保留确认城市，不收集候选城市
                        return result

        # 格式5: 城市开头 城市-岗位
        pattern = rf'^({self.city_pattern})[\s\-|]+'
        match = re.search(pattern, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                result.confirmed_city = standard_name
                result.candidate_cities = []  # 只保留确认城市，不收集候选城市
                return result

        # 格式6: 城市结尾 岗位-城市
        pattern = rf'[\s\-|/]+({self.city_pattern})$'
        match = re.search(pattern, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                result.confirmed_city = standard_name
                result.candidate_cities = []  # 只保留确认城市，不收集候选城市
                return result

        # 格式7: BOSS直聘格式 城市薪资【BOSS直聘】 或 城市数字-数字【...
        # 例如: "上海8-13K【BOSS直聘】" 或 "北京15-25K【..."
        boss_pattern3 = rf'({self.city_pattern})\d+[\d\-Kk]+【[^】]+】'
        match = re.search(boss_pattern3, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                result.confirmed_city = standard_name
                logger.info(f"从BOSS格式(城市薪资)提取到城市: {standard_name}")
                result.candidate_cities = []  # 只保留确认城市，不收集候选城市
                return result

        # ========== 未找到确认城市，不收集候选城市 ==========
        result.candidate_cities = []
        return result

    def _extract_from_body(self, body: str) -> CityExtractionResult:
        """从邮件正文提取城市（区分确认和候选）

        确认城市来源：
        - 期望工作地点关键词
        - 应聘/期望关键词后的城市

        候选城市来源：
        - 全文统计出现最多的城市
        """
        result = CityExtractionResult()

        if not body:
            return result

        body = body[:5000]

        # ========== 确认城市提取 ==========

        # 期望工作地点等关键词
        location_keywords = [
            r'期望工作地点[:：\s]*({self.city_pattern})',
            r'可工作城市[:：\s]*({self.city_pattern})',
            r'工作地点[:：\s]*({self.city_pattern})',
            r'期望城市[:：\s]*({self.city_pattern})',
            r'求职地点[:：\s]*({self.city_pattern})',
        ]

        for pattern in location_keywords:
            match = re.search(pattern, body)
            if match:
                city_name = match.group(1)
                standard_name = get_standard_city_name(city_name)
                if standard_name:
                    result.confirmed_city = standard_name
                    return result

        # 应聘/期望关键词后的城市
        for keyword in self.application_keywords:
            pattern = rf'{keyword}[^。]*?({self.city_pattern})'
            match = re.search(pattern, body)
            if match:
                # get_standard_city_name 现在可以处理 tuple（来自嵌套捕获组）
                city_name = match.group(1)
                standard_name = get_standard_city_name(city_name)
                if standard_name:
                    result.confirmed_city = standard_name
                    return result

        # ========== 候选城市提取 ==========
        result.candidate_cities = self._extract_all_cities_from_text(body)
        return result

    def _extract_from_resume(self, text: str) -> CityExtractionResult:
        """从简历文本提取城市（区分确认和候选）

        确认城市来源：
        - 期望工作地点关键词
        - 现居住地关键词

        候选城市来源：
        - 工作经历中的城市（公司名前缀）
        - 全文统计出现>=3次的城市
        """
        result = CityExtractionResult()

        if not text:
            return result

        text = text[:8000]

        # ========== 确认城市提取 ==========

        # 期望工作地点等关键词
        location_patterns = [
            r'期望工作地点[:：\s]*({self.city_pattern})',
            r'期望城市[:：\s]*({self.city_pattern})',
            r'求职地点[:：\s]*({self.city_pattern})',
            r'意向城市[:：\s]*({self.city_pattern})',
            r'期望工作地[:：\s]*({self.city_pattern})',
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                city_name = match.group(1)
                standard_name = get_standard_city_name(city_name)
                if standard_name:
                    result.confirmed_city = standard_name
                    return result

        # 现居住地等关键词
        residence_patterns = [
            r'现居住地[:：\s]*({self.city_pattern})',
            r'居住地[:：\s]*({self.city_pattern})',
            r'所在地[:：\s]*({self.city_pattern})',
            r'目前所在地[:：\s]*({self.city_pattern})',
        ]

        for pattern in residence_patterns:
            match = re.search(pattern, text)
            if match:
                city_name = match.group(1)
                standard_name = get_standard_city_name(city_name)
                if standard_name:
                    result.confirmed_city = standard_name
                    return result

        # ========== 候选城市提取 ==========
        result.candidate_cities = self._extract_all_cities_from_text(text, min_count=3)
        return result

    # ========== 辅助方法 ==========

    def _extract_all_cities_from_text(self, text: str, exclude: str = None,
                                       min_count: int = 1) -> List[str]:
        """从文本中提取所有出现的城市

        Args:
            text: 要分析的文本
            exclude: 要排除的城市名
            min_count: 最小出现次数

        Returns:
            城市列表（已去重）
        """
        if not text:
            return []

        # 使用 finditer 获取完整匹配（避免捕获组问题）
        cities = []
        for match in re.finditer(self.city_pattern, text):
            cities.append(match.group(0))  # 获取完整匹配

        if not cities:
            return []

        # 标准化所有城市名
        standard_cities = []
        for city_name in cities:
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                if exclude and standard_name == exclude:
                    continue
                standard_cities.append(standard_name)

        if not standard_cities:
            return []

        # 统计出现次数
        from collections import Counter
        city_counter = Counter(standard_cities)

        # 返回满足最小出现次数的城市，去重
        result = []
        seen = set()
        for city, count in city_counter.items():
            if count >= min_count and city not in seen:
                result.append(city)
                seen.add(city)

        return result

    def _extract_candidates_from_body(self, body: str) -> List[str]:
        """从邮件正文提取候选城市"""
        return self._extract_all_cities_from_text(body[:5000] if body else '')

    def _extract_candidates_from_resume(self, text: str) -> List[str]:
        """从简历文本提取候选城市"""
        candidates = []

        if not text:
            return candidates

        text = text[:8000]

        # 从工作经历中的公司名前缀提取
        work_patterns = [
            rf'({self.city_pattern})[^。]*?公司',
            rf'({self.city_pattern})[^。]*?科技',
            rf'({self.city_pattern})[^。]*?有限',
        ]

        for pattern in work_patterns:
            # 使用 finditer 避免 re.findall 返回 tuple 的���题
            for match in re.finditer(pattern, text):
                city_name = match.group(1)  # 获取城市捕获组
                standard_name = get_standard_city_name(city_name)
                if standard_name and standard_name not in candidates:
                    candidates.append(standard_name)

        # 从全文统计提取
        candidates.extend(self._extract_all_cities_from_text(text, min_count=3))

        return list(dict.fromkeys(candidates))  # 去重
