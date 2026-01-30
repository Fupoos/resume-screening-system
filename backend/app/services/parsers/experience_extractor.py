"""工作经历提取器 - 从简历文本中提取工作经历信息"""
import re
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ExperienceExtractor:
    """工作经历提取器

    从简历文本中提取工作经历信息，包括：
    - 公司名称
    - 职位
    - 工作时间
    - 工作年限
    """

    @staticmethod
    def extract_work_experience(text: str) -> List[Dict]:
        """提取工作经历 - 改进版V3（全文档搜索）

        支持格式：
        1. 时间和公司在同一行：2020.09-2024.06 XX公司
        2. 公司名在前，时间在后：
           XX公司
           2020.09-2024.06
        3. 公司名→职位→时间（三行结构）：
           XX公司
           职位
           2020.09-2024.06

        策略：全文档搜索，找到所有时间行，然后向前查找公司名
        """
        work_list = []

        # 时间格式正则模式（支持多种格式）
        time_patterns = [
            r'(\d{4})\.(\d{1,2})\s*[-.—至到]\s*(\d{4})\.(\d{1,2})',  # 2020.09-2024.06
            r'(\d{4})年(\d{1,2})月\s*[-.—至到]\s*(\d{4})年(\d{1,2})月',  # 2020年09月-2024年06月
            r'(\d{4})\s*[-.—至到]\s*(\d{4})',  # 2020-2024
            r'(\d{4})\.(\d{1,2})\s*[-.—至到]\s*至今',  # 2020.09-至今
            r'(\d{4})年\s*[-.—至到]\s*至今',  # 2020年-至今
            r'(\d{4})年(\d{1,2})月\s*[-.—至到]\s*至今',  # 2023年7月-至今
        ]

        # 公司名识别模式
        company_patterns = [
            r'.*公司.*',  # 包含"公司"
            r'.*科技.*',  # 包含"科技"
            r'.*有限.*',  # 包含"有限"
            r'.*集团.*',  # 包含"集团"
            r'.*银行.*',  # 包含"银行"
            r'.*医院.*',  # 包含"医院"
            #".*学校.*"，避免把学校误识别为公司
        ]

        non_work_patterns = [
            r'.*学院.*',  # 包含"学院"
            r'.*大学.*',  # 包含"大学"
            r'.*专业.*',  # 包含"专业"
            r'.*课程.*',  # 包含"课程"
            r'.*学习.*',  # 包含"学习"
            r'.*教学.*',  # 包含"教学"
            r'.*教育.*',  # 包含"教育"
            r'.*培训.*',  # 包含"培训"
        ]

        non_work_majors = [
            '应用化学', '供应链管理', '工商管理', '计算机科学', '软件工程',
            '电子信息', '机械工程', '土木工程', '材料科学', '生物工程',
            '市场营销', '人力资源管理', '财务管理', '会计学', '金融学',
            '国际贸易', '电子商务', '物流管理', '信息管理', '统计学',
            '应用数学', '应用物理', '汉语言文学', '英语', '日语',
            '工商管理', '公共管理', '行政管理', '社会学', '心理学',
        ]

        # 职位关键词
        position_keywords = ['工程师', '专员', '经理', '总监', '主管', '助理', '顾问',
                           '开发', '设计', '测试', '运营', '销售', '财务', '人事', '行政',
                           '分析师', '架构师', '产品经理', '执行', 'PM']

        internship_keywords = ['实习', '兼职', '见习', '实训', '校园']

        # 查找工作经历段落（用于确定搜索范围）
        keywords = ['工作经历', '工作经验', '职业经历', '工作']
        internship_section_keywords = ['实习经历', '实习工作', '实习经验', '见习经历']
        lines = text.split('\n')
        start_idx = None
        end_idx = len(lines)

        def is_section_header(line_text, keyword):
            """检查是否为section标题（独立成行，或只跟冒号）"""
            if line_text == keyword:
                return True
            for colon in ['：', ':']:
                if line_text.startswith(keyword + colon):
                    after_colon = line_text[len(keyword) + len(colon):].strip()
                    if not after_colon:
                        return True
            return False

        # 优先检查是否是实习section，如果是则直接返回空列表
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(is_section_header(line_stripped, kw) for kw in internship_section_keywords):
                return []  # 实习section不提取工作经历
            if any(is_section_header(line_stripped, kw) for kw in keywords):
                start_idx = i
                break


        # 定义搜索范围：如果有"工作经历"标题，从标题前搜索到标题后
        # 如果没有标题，全文档搜索
        if start_idx is not None:
            # 从标题前50行开始，到标题后100行结束
            search_start = max(0, start_idx - 50)
            search_end = min(len(lines), start_idx + 100)
        else:
            # 全文档搜索
            search_start = 0
            search_end = len(lines)

        # 第一步：找到所有包含时间的行索引
        time_lines = {}  # {行索引: 时间字符串}
        for i in range(search_start, search_end):
            line = lines[i].strip()
            if not line:
                continue

            # 如果在"工作经历"之后，遇到新段落停止
            if start_idx is not None and i > start_idx:
                if any(keyword in line for keyword in ['项目经验', '教育背景', '技能', '联系方式', '自我评价']):
                    break

            # 检查是否包含时间
            for pattern in time_patterns:
                match = re.search(pattern, line)
                if match:
                    time_lines[i] = match.group(0)
                    break

        # 第二步：对每个时间行，提取公司名和职位
        processed_indices = set()  # 记录已处理的行索引
        # section header黑名单（不应当被误识别为公司名）
        section_headers = {'工作经历', '项目经历', '项目经验', '实习经历', '实习工作',
                           '教育背景', '教育经历', '学习经历', '技能', '专业技能',
                           '联系方式', '自我评价', '个人优势', '获奖情况', '证书'}

        for time_idx in sorted(time_lines.keys()):
            if time_idx in processed_indices:
                continue

            duration = time_lines[time_idx]
            time_line = lines[time_idx].strip()

            # 优先策略：从时间行本身提取公司名和职位
            # 格式：公司 职位 时间（如"百望股份有限公司 销售经理 2023.05-2025.09"）
            company = ''
            position = ''

            # 先尝试从时间行提取
            time_line_clean = time_line
            for pattern in time_patterns:
                time_line_clean = re.sub(pattern, '', time_line_clean).strip()

            if time_line_clean and len(time_line_clean) > 3:
                # 分析时间行剩余内容，提取公司和职位
                # 尝试分离：最后一部分通常是职位，前面是公司
                parts = time_line_clean.split()

                # 检查是否包含职位关键词（作为分隔点）
                position_idx = -1
                for i, part in enumerate(parts):
                    for pk in position_keywords:
                        if pk in part:
                            position_idx = i
                            # 提取完整职位（可能包含多个词）
                            position_candidate = ' '.join(parts[i:])
                            # 验证：如果后面紧跟时间格式，那这不是职位
                            has_time_after = False
                            for pattern in time_patterns:
                                if re.search(pattern, ' '.join(parts[i:])):
                                    has_time_after = True
                                    break
                            if not has_time_after:
                                position = part
                                # 职位之前的是公司名
                                company_candidate = ' '.join(parts[:i]).strip()
                                if company_candidate and len(company_candidate) > 2:
                                    company = company_candidate
                            break
                    if position:
                        break

                # 如果没找到职位，尝试其他方式
                if not company and not position:
                    # 检查是否包含公司关键词
                    if any(re.search(p, time_line_clean) for p in company_patterns):
                        # 有公司关键词，整个内容可能是公司名
                        company = time_line_clean
                    elif 3 < len(time_line_clean) < 60:
                        # 适中长度，可能是公司名
                        # 排除纯描述性文本
                        if not any(time_line_clean.startswith(w) for w in ['负责', '内容', '业绩', '描述']):
                            company = time_line_clean

            # 如果时间行没有提取到公司名，向前查找
            if not company:
                search_back_start = max(search_start, time_idx - 5)

                for j in range(time_idx - 1, search_back_start - 1, -1):
                    if j in processed_indices:
                        break  # 遇到已处理的工作经历，停止

                    line = lines[j].strip()
                    if not line:
                        continue

                    # 跳过section header（关键修复）
                    if line in section_headers:
                        continue

                    work_desc_prefixes = ['负责', '协助', '主导', '参与', '完成', '执行',
                                         '开展', '跟进', '管理', '策划', '设计', '开发']
                    if any(line.startswith(prefix) for prefix in work_desc_prefixes):
                        continue

                    # 跳过明显不是公司名的行
                    skip_patterns = ['项目职责', '项目业绩', '主要职责', '工作内容', '业绩',
                                   '求职意向', '期望薪资', '期望城市', '内容', '描述']
                    if any(skip in line for skip in skip_patterns):
                        continue

                # 检查是否是公司名（放宽条件）
                if not company:
                    # 优先匹配包含明确公司关键词的
                    if any(re.search(p, line) for p in company_patterns):
                        company = line
                        continue
                    # 优先级2：包含"|"的行通常是"职位 | 公司"格式
                    if '|' in line and 3 < len(line) < 100:
                        company = line
                        continue
                    # 次优：排除纯职位行，其他适中长度的行都可能是公司名
                    is_position_only = any(pk in line for pk in position_keywords) and len(line) < 20

                    if not is_position_only and 3 < len(line) < 60:
                        # 看起来像公司名或组织名
                        company = line
                        continue

                # 检查是否包含职位关键词（但不是公司名）
                if not position and not any(re.search(p, line) for p in company_patterns):
                    for keyword in position_keywords:
                        if keyword in line:
                            position = keyword
                            break

            # 过滤教育相关和实习经历
            is_education_related = False
            if company:
                # 检查是否匹配非工作模式
                for p in non_work_patterns:
                    if re.search(p, company):
                        is_education_related = True
                        break
                if company in non_work_majors:
                    is_education_related = True
                if any(kw in time_line for kw in ['本科', '硕士', '博士', '研究生', '学位']):
                    is_education_related = True

            if position:
                if any(kw in position for kw in internship_keywords):
                    is_education_related = True

            if any(kw in time_line for kw in internship_keywords + ['教育', '学习', '课程']):
                is_education_related = True


            # 创建工作记录（过滤掉教育相关和实习经历）
            if not is_education_related and (company or position):
                work_entry = {
                    'company': company if company else '',
                    'position': position,
                    'duration': duration,
                    'years': 0,
                    'responsibilities': ''
                }
                work_entry['years'] = ExperienceExtractor.extract_years_from_duration(duration)
                work_list.append(work_entry)
                processed_indices.add(time_idx)

                # 最多取5条
                if len(work_list) >= 5:
                    break

        return work_list

    @staticmethod
    def calculate_work_years(work_experience: List[Dict]) -> int:
        """计算工作年限 - 改进版（累加所有工作经历）"""
        total_years = 0

        for work in work_experience:
            # 使用新方法提取年限
            years = ExperienceExtractor.extract_years_from_duration(work.get('duration', ''))
            total_years += years

        return int(total_years)

    @staticmethod
    def extract_years_from_duration(duration: str) -> int:
        """从时间段字符串提取工作年限（简化版：按年份计算）

        支持格式：
        - 2020.09-2024.06 → 4年
        - 2020年09月-2024年06月 → 4年
        - 2020-2024 → 4年
        - 2020.09-至今 → 当前年份 - 2020

        Args:
            duration: 时间段字符串

        Returns:
            工作年限（年）
        """
        if not duration:
            return 0

        current_year = datetime.now().year

        # 辅助函数：验证年份是否合理（1900-2100）
        def is_valid_year(year: int) -> bool:
            return 1900 <= year <= 2100

        # 模式1: 2020.09-2024.06 或 2020年09月-2024年06月
        match = re.search(r'(\d{4})[\.年]\d{1,2}[月]?\s*[-.—至到]\s*(\d{4})[\.年]\d{1,2}[月]?', duration)
        if match:
            start_year = int(match.group(1))
            end_year = int(match.group(2))
            # 验证年份合理性
            if is_valid_year(start_year) and is_valid_year(end_year) and start_year <= end_year:
                return end_year - start_year

        # 模式2: 2020-2024（需要更严格的验证，避免匹配薪资）
        match = re.search(r'(\d{4})\s*[-.—至到]\s*(\d{4})(?![0-9])', duration)
        if match:
            start_year = int(match.group(1))
            end_year = int(match.group(2))
            # 验证年份合理性
            if is_valid_year(start_year) and is_valid_year(end_year) and start_year <= end_year:
                years = end_year - start_year
                # 如果计算出的年限超过60年，可能不是工作经历
                if years <= 60:
                    return years

        # 模式3: 2020.09-至今 或 2020年-至今
        match = re.search(r'(\d{4})[\.年]?\d{0,2}[月]?\s*[-.—至到]\s*至今', duration)
        if match:
            start_year = int(match.group(1))
            # 验证年份合理性
            if is_valid_year(start_year):
                years = current_year - start_year
                # 如果计算出的年限超过60年，可能不是工作经历
                if years <= 60:
                    return years

        # 如果无法解析，返回0
        return 0
