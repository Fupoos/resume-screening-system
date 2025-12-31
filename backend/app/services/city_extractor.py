"""城市提取服务 - 从邮件主题、正文、简历中提取城市信息"""
import re
import logging
from typing import Optional
from app.data.cities import ALL_CITIES, CITY_ALIASES, get_standard_city_name

logger = logging.getLogger(__name__)


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

    def extract_city(self, email_subject: str = '', email_body: str = '', resume_text: str = '') -> Optional[str]:
        """按优先级提取城市：主题 > 正文 > 简历

        Args:
            email_subject: 邮件主题
            email_body: 邮件正文
            resume_text: 简历文本

        Returns:
            提取的城市名称（标准名称），如果未找到则返回 None
        """
        # 优先级1: 从邮件主题提取（优先匹配"应聘|申请|期望"后面的城市）
        city = self._extract_from_subject(email_subject)
        if city:
            logger.info(f"从邮件主题提取到城市: {city}")
            return city

        # 优先级2: 从邮件正文提取
        city = self._extract_from_body(email_body)
        if city:
            logger.info(f"从邮件正文提取到城市: {city}")
            return city

        # 优先级3: 从简历文本提取
        city = self._extract_from_resume(resume_text)
        if city:
            logger.info(f"从简历文本提���到城市: {city}")
            return city

        logger.debug("未能从任何来源提取到城市信息")
        return None

    def _extract_from_subject(self, subject: str) -> Optional[str]:
        """从邮件主题提取城市

        支持格式:
        - "应聘北京Python工程师" -> "北京"
        - "上海-HR岗" -> "上海"
        - "期望工作地点：深圳后端开发" -> "深圳"
        - "南京 | Java开发工程师" -> "南京"

        Args:
            subject: 邮件主题

        Returns:
            提取的城市名称，如果未找到则返回 None
        """
        if not subject:
            return None

        subject = subject.strip()

        # 策略1: 优先匹配"应聘|申请|期望|求职意向|投递"后面的城市
        for keyword in self.application_keywords:
            # 匹配 "关键词 城市" 或 "关键词城市" 或 "关键词-城市"
            patterns = [
                rf'{keyword}[:：\s\-]*({self.city_pattern})',  # 应聘:北京 或 应聘北京
                rf'({self.city_pattern})[:：\s\-]*{keyword}',  # 北京:应聘
            ]

            for pattern in patterns:
                match = re.search(pattern, subject)
                if match:
                    city_name = match.group(1)
                    standard_name = get_standard_city_name(city_name)
                    if standard_name:
                        return standard_name

        # 策略2: 匹配"城市-岗位"或"城市|岗位"格式
        # 例如: "北京-HR岗", "上海 | Java开发"
        pattern = rf'^({self.city_pattern})[\s\-|]+'
        match = re.search(pattern, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                return standard_name

        # 策略3: 匹配"岗位-城市"格式
        # 例如: "Python工程师-北京", "HR专员 / 上海"
        pattern = rf'[\s\-|/]+({self.city_pattern})$'
        match = re.search(pattern, subject)
        if match:
            city_name = match.group(1)
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                return standard_name

        # 策略4: 全局搜索（如果主题中只有一个城市）
        cities = re.findall(self.city_pattern, subject)
        if len(cities) == 1:
            city_name = cities[0]
            standard_name = get_standard_city_name(city_name)
            if standard_name:
                return standard_name

        return None

    def _extract_from_body(self, body: str) -> Optional[str]:
        """从邮件正文提取城市

        支持格式:
        - "期望工作地点：深圳" -> "深圳"
        - "可工作城市: 北京、上海" -> "北京"（第一个）
        - "应聘广州岗位" -> "广州"

        Args:
            body: 邮件正文

        Returns:
            提取的城市名称，如果未找到则返回 None
        """
        if not body:
            return None

        # 只检查前5000个字符（通常邮件正文的前半部分包含关键信息）
        body = body[:5000]

        # 策略1: 优先匹配"期望工作地点|可工作城市|工作地点"等关键词
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
                    return standard_name

        # 策略2: 匹配"应聘/申请/期望"关键词附近的城市
        for keyword in self.application_keywords:
            # 匹配关键词后50个字符内的城市
            pattern = rf'{keyword}[^。]{0,50}?({self.city_pattern})'
            matches = re.findall(pattern, body)
            if matches:
                city_name = matches[0]  # 取第一个匹配
                standard_name = get_standard_city_name(city_name)
                if standard_name:
                    return standard_name

        # 策略3: 统计所有出现的城市，选择出现次数最多的
        cities = re.findall(self.city_pattern, body)
        if cities:
            # 标准化所有城市名
            standard_cities = [get_standard_city_name(city) for city in cities]
            # 过滤掉None
            standard_cities = [city for city in standard_cities if city]
            # 统计出现次数
            from collections import Counter
            city_counter = Counter(standard_cities)
            # 返回出现次数最多的城市
            if city_counter:
                most_common = city_counter.most_common(1)[0][0]
                return most_common

        return None

    def _extract_from_resume(self, text: str) -> Optional[str]:
        """从简历文本提取城市

        支持格式:
        - "期望工作地点：上海" -> "上海"
        - "现居住地：北京市" -> "北京"
        - "工作经历：北京XX科技有限公司" -> "北京"

        Args:
            text: 简历文本

        Returns:
            提取的城市名称，如果未找到则返回 None
        """
        if not text:
            return None

        # 只检查前8000个字符（通常个人信息在前半部分）
        text = text[:8000]

        # 策略1: 优先匹配"期望工作地点|求职意向|期望城市"等关键词
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
                    return standard_name

        # 策略2: 匹配"现居住地|居住地|所在地"等关键词
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
                    return standard_name

        # 策略3: 从工作经历中提取（查找"城市XX公司"模式）
        # 通常格式：北京XX科技有限公司、上海XX集团
        work_patterns = [
            rf'({self.city_pattern})[^。]{0,30}?公司',
            rf'({self.city_pattern})[^。]{0,30}?科技',
            rf'({self.city_pattern})[^。]{0,30}?有限',
        ]

        for pattern in work_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 取第一个出现的工作地点
                city_name = matches[0]
                standard_name = get_standard_city_name(city_name)
                if standard_name:
                    return standard_name

        # 策略4: 统计所有出现的城市，选择出现次数最多的
        cities = re.findall(self.city_pattern, text)
        if cities:
            # 标准化所有城市名
            standard_cities = [get_standard_city_name(city) for city in cities]
            # 过滤掉None
            standard_cities = [city for city in standard_cities if city]
            # 统计出现次数
            from collections import Counter
            city_counter = Counter(standard_cities)
            # 返回出现次数最多的城市（如果出现次数>=3）
            if city_counter:
                most_common = city_counter.most_common(1)[0]
                if most_common[1] >= 3:  # 至少出现3次
                    return most_common[0]

        return None
