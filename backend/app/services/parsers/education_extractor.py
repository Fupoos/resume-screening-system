"""教育背景提取器 - 从简历文本中���取学历信息"""
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class EducationExtractor:
    """教育背景提取器

    从简历文本中提取教育背景信息，包括：
    - 学校名称
    - 学历（博士、硕士、本科等）
    - 专业
    - 学习时间
    """

    @staticmethod
    def extract_education(text: str) -> List[Dict]:
        """提取教育背景 - 增强版 V2

        支持格式：
        1. 上海师范大学
           会计 / 硕士

        2. 本科 | 上海大学 | 计算机

        3. 2020.09-2024.06 合肥师范学院 财务管理 本科

        4. 东北农业大学 211
           软件工程(本科)  <- 括号格式

        5. 2022.09 ~ 2026.07
           东北农业大学
           软件工程(本科)

        6. 全文搜索模式（如果没有找到"教育背景"标题）
        """
        education_list = []

        # 教育背景关键词（用于定位教育背景段落，不包含"学历"因为"学历"可能出现在数据行中）
        keywords = ['教育背景', '学习经历', '教育经历', '学历背景', '专业背景', 'EDUCATIONAL BACKGROUND', 'EDUCATION', 'EDUCATION HISTORY']

        # 学历关键词（用于提取学历）- 按优先级排序（中英文双语）
        degree_keywords = ["博士研究生", "博士", "硕士研究生", "研究生", "硕士", "学士", "本科", "大专", "专科", "高中", "中专",
                          "Ph.D", "PhD", "Doctor", "Doctorate",  # 英文博士
                          "Master", "Masters", "M.B.A", "MBA",  # 英文硕士
                          "Bachelor", "Bachelors", "B.S", "B.A", "B.Sc", "BBA",  # 英文本科
                          "Associate", "College"]  # 英文大专

        # 非学历括号关键词（这些括号内容不是学历，需要清理后再提取学校名）
        non_degree_parentheses = ["全英", "辅修", "双学位", "第二专业", "英文授课", "中外合作",
                                  "全日制", "非全日制", "在职", "定向", "委培", "自考",
                                  "函授", "夜大", "成人", "网络", "开放", "高职", "中职"]

        # 学历正则模式（支持括号格式，包括带前缀的如"(工学硕士)"，以及英文格式）
        degree_patterns = [
            # 中文模式
            r'\((?:[^\)]*?)?(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)\)',  # (本科)或(工学硕士)
            r'（(?:[^）]*?)?(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)）',  # （本科）或（工学硕士）
            r'\s(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)\s',  # 空格包围
            r'/(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)',  # /本科
            r'\|(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)',  # |本科
            # 英文模式
            r'\b(Ph\.D|PhD|Doctor|Doctorate|Masters?|Master|M\.B\.A|MBA|Bachelors?|Bachelor|B\.S|B\.A|B\.Sc|BBA|Associate|College)\b',  # 英文学历
            r'/(Masters?|Master|Bachelors?|Bachelor|Ph\.D|PhD)',  # /Master or /Bachelor
        ]

        lines = text.split('\n')
        start_idx = None

        # 查找教育背景段落
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in keywords):
                start_idx = i
                break

        if start_idx is None:
            # 如果没找到明确的标题，尝试通过学历关键词定位
            for i, line in enumerate(lines):
                if any(edu in line for edu in degree_keywords):
                    start_idx = max(0, i - 2)
                    break

        # 特殊格式检查：在前几行查找"年龄 - 学历 - 工作年限"格式
        # 例如：36 岁 - 本科 - 工作 13 年 7 个月
        if not education_list:
            for i, line in enumerate(lines[:20]):  # 只检查前20行
                line = line.strip()
                # 匹配格式：数字 岁 - 学历 - 工作 或类似格式
                match = re.search(r'(\d+)\s*岁\s*[-—–]\s*(本科|硕士|博士|大专|专科|高中|中专)', line)
                if match:
                    degree = match.group(2)
                    education = {
                        'school': '',
                        'degree': degree,
                        'major': '',
                        'duration': ''
                    }
                    education_list.append(education)
                    # 找到学历后，使用找到的行作为起始点
                    start_idx = i
                    break

        if start_idx is None:
            # 后处理：从school字段中提取degree并清理school名称
            education_list = EducationExtractor._post_process_education(education_list)
            return education_list

        # 新增：如果在找到"教育背景"标题，可能教育信息在标题之前（如余惜缘的简历）
        # 先向前搜索50行，查找教育模式
        if start_idx > 0 and any(keyword in lines[start_idx] for keyword in keywords):
            backward_start = max(0, start_idx - 50)
            processed_school_lines = set()  # 记录已处理的学校行，避免重复

            for j in range(start_idx - 1, backward_start - 1, -1):
                line = lines[j].strip()
                if not line:
                    continue

                # 遇到新段落停止
                if any(keyword in line for keyword in ['工作经历', '项目经验', '求职意向', '基本信息', '联系方式', '姓名']):
                    break

                # 检查是否包含学校名（"大学"或"学院"）
                if '大学' in line or '学院' in line:
                    # 避免重复处理同一行
                    if j in processed_school_lines:
                        continue
                    processed_school_lines.add(j)

                    education = {
                        'school': '',
                        'degree': '',
                        'major': '',
                        'duration': ''
                    }

                    # 优先处理0: 检查"学校|学历(专业)"格式（如"多伦多大学|文学学士(艺术史)"）
                    # 支持;分隔多个学校，如"学校1|学历1(专业1);学校2|学历2"
                    pipe_format_processed = False  # 标记是否已处理过|格式
                    if '|' in line:
                        # 先用;分割多个学校
                        school_entries = line.split(';')
                        for entry in school_entries:
                            entry = entry.strip()
                            if '|' in entry:
                                parts = entry.split('|')
                                if len(parts) >= 2:
                                    school_part = parts[0].strip()
                                    degree_major_part = parts[1].strip()

                                    # 提取学校名（以"大学"或"学院"结尾）
                                    if '大学' in school_part or '学院' in school_part:
                                        for uni_kw in ['大学', '学院', 'University', 'College']:
                                            if uni_kw in school_part:
                                                idx = school_part.index(uni_kw)
                                                education['school'] = school_part[:idx + len(uni_kw)].strip()
                                                break

                                        # 解析学历和专业（格式：文学学士(艺术史 / 经济学)）
                                        # 先检查括号内的内容作为专业
                                        major_match = re.search(r'\(([^)]+)\)', degree_major_part)
                                        if major_match:
                                            education['major'] = major_match.group(1).strip()
                                            # 移除括号部分，剩余作为学历
                                            degree_part = re.sub(r'\([^)]+\)', '', degree_major_part).strip()
                                            if degree_part:
                                                education['degree'] = degree_part
                                        else:
                                            # 没有括���，整个部分可能是学历
                                            education['degree'] = degree_major_part

                                        # 如果成功提取到学校和学历/专业，添加到列表并继续处理下一个
                                        if education['school'] and (education['degree'] or education['major']):
                                            education_list.append(education)
                                            pipe_format_processed = True  # 标记已处理
                                            education = {
                                                'school': '',
                                                'degree': '',
                                                'major': '',
                                                'duration': ''
                                            }
                                        continue  # 处理下一个school entry

                    # 如果已经处理过|格式，跳过后续处理
                    if pipe_format_processed:
                        continue

                    # 优先处理：当前行包含括号格式的学历（如"华东理工大学 工业催化(工学硕士)"）
                    has_bracket_degree = False
                    for pattern in degree_patterns:
                        match = re.search(pattern, line)
                        if match:
                            has_bracket_degree = True
                            education['degree'] = match.group(1)
                            # 提取括号前的部分（学校 + 专业）
                            before_paren = re.sub(r'[()（）][^()（）]*', '', line).strip()
                            # 分离学校名和专业
                            for uni_kw in ['大学', '学院', 'University', 'College']:
                                if uni_kw in before_paren:
                                    idx = before_paren.index(uni_kw)
                                    if idx + len(uni_kw) < len(before_paren):
                                        education['school'] = before_paren[:idx + len(uni_kw)].strip()
                                        education['major'] = before_paren[idx + len(uni_kw):].strip()
                                    else:
                                        education['school'] = before_paren.strip()
                                    break
                            break

                    # 如果当前行没有括号格式，检查是否是"•"分隔格式
                    if not has_bracket_degree:
                        # 检查"学校 • 内设学院 • 专业"格式
                        if ' • ' in line or ' · ' in line:
                            parts = re.split(r' [•·|] ', line)
                            if len(parts) >= 1:
                                education['school'] = parts[0].strip()
                                # 查找专业
                                for i, part in enumerate(parts[1:], 1):
                                    part = part.strip()
                                    # 跳过GPA、Rank等非专业信息
                                    if part.startswith('GPA') or part.startswith('Rank') or ':' in part:
                                        continue
                                    # 检查是否看起来像专业名（2-10个汉字，不含"学院"等）
                                    if '学院' not in part and len(part) >= 2 and len(part) <= 15:
                                        if re.match(r'^[\u4e00-\u9fa5（）()]+$|^[A-Za-z\s&/]+$', part):
                                            education['major'] = part
                                            break
                        else:
                            education['school'] = line

                        # 向前搜索duration（从j-1往回找）
                        for k in range(j - 1, max(0, j - 5), -1):
                            prev_line = lines[k].strip()
                            if not prev_line:
                                continue
                            # 检查是否包含时间格式
                            time_match = re.search(r'(\d{4})\s*[-.年—]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', prev_line)
                            if time_match:
                                education['duration'] = time_match.group(0)
                                break

                        # 如果找到了duration，尝试推断degree
                        if education['duration'] and not education['degree']:
                            year_match = re.findall(r'(\d{4})', education['duration'])
                            if len(year_match) == 2:
                                start_year, end_year = int(year_match[0]), int(year_match[1])
                                duration_years = end_year - start_year
                                if duration_years >= 3 and duration_years <= 5:
                                    education['degree'] = '本科'
                                elif duration_years >= 1 and duration_years <= 3:
                                    education['degree'] = '硕士'
                                elif duration_years >= 5:
                                    education['degree'] = '博士'

                        # 如果还没有degree，向后搜索（从j+1到start_idx）查找学历和专业
                        if not education['degree']:
                            for k in range(j + 1, min(start_idx, len(lines))):  # 只搜索到start_idx（不包括标题行）
                                next_line = lines[k].strip()
                                if not next_line:
                                    continue

                                # 检查是否是新的section
                                if any(keyword in next_line for keyword in ['工作经历', '项目经验', '求职意向', '基本信息', '联系方式', '资格证书', '技能', '荣誉', '奖项']):
                                    break

                                # 如果遇到另一个学校行，停止（说明是另一个教育经历）
                                if ('大学' in next_line or '学院' in next_line) and k != j:
                                    # 检查这行是否包含括号格式学历
                                    has_degree = False
                                    for pattern in degree_patterns:
                                        if re.search(pattern, next_line):
                                            has_degree = True
                                            break
                                    # 如果没有括号格式学历，可能是另一个独立的学校行，停止
                                    if not has_degree:
                                        break
                                    # 如果有括号格式学历，这是另一个教育经历，停止当前处理的向后搜索
                                    break

                                # 优先检查：纯学历关键词（如"本科"、"硕士"）
                                if not education['degree'] and next_line in degree_keywords:
                                    education['degree'] = next_line

                                # 检查行中是否包含学历关键词（如"本科学历"等）
                                if not education['degree']:
                                    for degree in degree_keywords:
                                        if degree in next_line:
                                            education['degree'] = degree
                                            break

                                # 检查括号格式的学历
                                for pattern in degree_patterns:
                                    match = re.search(pattern, next_line)
                                    if match:
                                        education['degree'] = match.group(1)
                                        # 提取专业（括号前的部分）
                                        before_paren = re.sub(r'[()（）][^()（）]*', '', next_line).strip()
                                        # 如果括号前有内容且不是学校名，作为专业
                                        if before_paren and before_paren != education['school']:
                                            education['major'] = before_paren
                                        break

                                # 提取时间
                                if not education['duration']:
                                    time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', next_line)
                                    if time_match:
                                        education['duration'] = time_match.group(0)

                                # 如果已找到学历，停止向后搜索
                                if education['degree']:
                                    break

                    # 如果找到有效的education，添加到列表
                    if education['school']:
                        education_list.append(education)
                        if len(education_list) >= 5:
                            break

            # 反转列表，使前面的学校排在前面
            education_list.reverse()

        # 解析教育经历（从start_idx开始向后搜索）
        i = start_idx
        processed_school_lines_forward = set()  # 记录forward搜索中已处理的学校行，避免重复
        while i < min(start_idx + 100, len(lines)):  # 扩大搜索范围到100行
            # 跳过纯空格/空行（继续向后搜索）
            if not lines[i].strip():
                i += 1
                continue

            line = lines[i].strip()

            # 跳过空行和标题行
            if not line or any(keyword in line for keyword in keywords):
                i += 1
                continue

            # 遇到新段落，停止（但不包括"实习经历"，因为有些简历的教育信息在实习经历之后）
            # 注意：不停止"专业技能"/"技能"，因为有些简历的教育信息在专业技能之后
            if any(keyword in line for keyword in ['工作经历', '项目经验', '联系方式']):
                break

            education = None

            # ========== 模式-2: "学校名"单独一行 + "学历|专业"下一行 ==========
            # 例如：
            #   哥伦比亚大学(Columbia University)
            #   理学硕士|企业风险管理(Enterprise Risk Management)(硕士)
            if i + 1 < len(lines) and ('大学' in line or '学院' in line):
                next_line = lines[i + 1].strip()
                # 检查下一行是否是"学历|专业"格式（且不包含学校关键字，避免重复）
                if '|' in next_line and not ('大学' in next_line or '学院' in next_line):
                    parts = next_line.split('|')
                    if len(parts) >= 1:
                        # 提取学校名（当前行）
                        education = {
                            'school': '',
                            'degree': '',
                            'major': '',
                            'duration': ''
                        }
                        # 学校名可能是：哥伦比亚大学 或 哥伦比亚大学(Columbia University)
                        for uni_kw in ['大学', '学院', 'University', 'College']:
                            if uni_kw in line:
                                idx = line.index(uni_kw)
                                # 提取学校名，然后清理前缀（时间等）
                                school_name = line[:idx + len(uni_kw)].strip()
                                # 移除时间前缀（如 "2024-09 ~ 2025-12 "）
                                school_name = re.sub(r'^[\d\s\-~年月日至今至到]+', '', school_name).strip()
                                # 移除英文括号内容（如 "(Columbia University)"）
                                school_name = re.sub(r'\([^)]*\)', '', school_name).strip()
                                education['school'] = school_name
                                break

                        # 解析学历和专业（下一行）
                        # 格式：理学硕士|企业风险管理(Enterprise Risk Management)(硕士)
                        degree_major_part = parts[0].strip()  # 理学硕士

                        # 检查是否有第二部分作为专业
                        if len(parts) >= 2:
                            major_part = parts[1].strip()  # 企业风险管理(Enterprise Risk Management)(硕士)
                            # 去掉括号中的额外信息
                            major_part = re.sub(r'\([^)]*\)', '', major_part).strip()
                            if major_part:
                                education['major'] = major_part

                        # 从第一部分提取学历
                        for degree in degree_keywords:
                            if degree in degree_major_part:
                                education['degree'] = degree
                                break

                        # 如果成功提取到学校和学历，添加到列表并跳过下一行
                        if education['school'] and education['degree']:
                            education_list.append(education)
                            i += 2  # 跳过当前行和下一行
                            continue

            # ========== 模式-1: "学校|学历(专业)"格式（如"多伦多大学|文学学士(艺术史)"）==========
            # 支持;分隔多个学校，如"学校1|学历1(专业1);学校2|学历2"
            pipe_format_handled = False  # 标记是否已处理过|格式
            if '|' in line and ('大学' in line or '学院' in line):
                # 先用;分割多个学校
                school_entries = line.split(';')
                for entry in school_entries:
                    entry = entry.strip()
                    if '|' in entry:
                        parts = entry.split('|')
                        if len(parts) >= 2:
                            school_part = parts[0].strip()
                            degree_major_part = parts[1].strip()

                            # 提取学校名（以"大学"或"学院"结尾）
                            if '大学' in school_part or '学院' in school_part:
                                education = {
                                    'school': '',
                                    'degree': '',
                                    'major': '',
                                    'duration': ''
                                }
                                for uni_kw in ['大学', '学院', 'University', 'College']:
                                    if uni_kw in school_part:
                                        idx = school_part.index(uni_kw)
                                        education['school'] = school_part[:idx + len(uni_kw)].strip()
                                        break

                                # 检查是否是三段式格式：学校 | 专业学位 | 学位 时间
                                # 例如：香港大学 | Master of Arts in AI Ethics and Society | 硕士   2025.9-2026.6
                                # 或：匹兹堡大学 | 硕士 宾夕法尼亚州,美国 | 2023/09 – 2025/12
                                if len(parts) >= 3:
                                    # 第二部分是专业/学位描述（如英文专业名）
                                    major_part = parts[1].strip()
                                    # 第三部分包含中文学历和时间
                                    degree_time_part = parts[2].strip()

                                    # 从第三部分提取时间（支持多种分隔符：-、.、年、—、至、到、/）
                                    time_match = re.search(r'(\d{4})\s*[-./年—/]\s*\d{1,2}\s*[-./年—至到/]\s*(\d{4}|\d{1,2}|至今)', degree_time_part)
                                    if time_match:
                                        education['duration'] = time_match.group(0)

                                    # 从第三部分提取中文学历
                                    for degree in degree_keywords:
                                        if degree in degree_time_part:
                                            education['degree'] = degree
                                            break

                                    # 如果第三部分没有中文学历，检查第二部分是否包含"学历 地点"格式
                                    if not education['degree'] and major_part:
                                        for degree in degree_keywords:
                                            if degree in major_part:
                                                education['degree'] = degree
                                                # 学历后的部分作为专业/地点备注
                                                location_part = major_part.replace(degree, '').strip()
                                                if location_part and not any(loc in location_part for loc in ['州', '省', '市', '县', '国', 'USA', 'US', 'UK', '中国', '美国', '英国', '加拿大']):
                                                    education['major'] = location_part
                                                break

                                    # 第二部分作为专业（如果第三部分已有中文学历且第二部分不含学历）
                                    if education['degree'] and major_part and not any(d in major_part for d in degree_keywords):
                                        education['major'] = major_part
                                    elif not education['degree'] and major_part:
                                        # 第三部分没有中文学历，第二部分作为学历
                                        education['degree'] = major_part
                                else:
                                    # 两段式格式：学校 | 学历专业
                                    # 首先检查 school_part 中是否包含学历（如"美国哥伦比亚大学硕士"）
                                    for degree in degree_keywords:
                                        if degree in school_part:
                                            education['degree'] = degree
                                            # 从学校名中移除学历，得到纯学校名
                                            education['school'] = school_part.replace(degree, '').strip()
                                            break

                                    # 解析学历和专业（格式：文学学士(艺术史 / 经济学)）
                                    # 或：专业学历 时间，如"统计学与经济学学士 2018.09 — 2022.05"
                                    major_match = re.search(r'\(([^)]+)\)', degree_major_part)
                                    if major_match:
                                        education['major'] = major_match.group(1).strip()
                                        # 移除括号部分，剩余作为学历
                                        degree_part = re.sub(r'\([^)]+\)', '', degree_major_part).strip()
                                        if degree_part:
                                            # 如果还没有degree，使用提取的
                                            if not education['degree']:
                                                education['degree'] = degree_part
                                    else:
                                        # 没有括号，尝试提取时间（如"2018.09 — 2022.05"）
                                        time_match = re.search(r'(\d{4})\s*[-.年—]\s*\d{1,2}\s*[-./年—至到]\s*(\d{4}|\d{1,2}|至今)', degree_major_part)
                                        if time_match:
                                            education['duration'] = time_match.group(0)
                                            # 移除时间后的部分
                                            remaining = degree_major_part[:time_match.start()].strip()
                                            # 从剩余部分提取学历和专业
                                            # 格式：统计学与经济学学士 -> major: 统计学与经济学, degree: 学士
                                            if not education['degree']:
                                                for degree in degree_keywords:
                                                    if degree in remaining:
                                                        education['degree'] = degree
                                                        # 学历前的部分是专业
                                                        major_part = remaining.replace(degree, '').strip()
                                                        if major_part:
                                                            education['major'] = major_part
                                                        break
                                            # 如果还没有专业，remaining作为专业
                                            if not education['major'] and remaining:
                                                education['major'] = remaining
                                        else:
                                            # 没有时间，整个部分可能是专业或学历
                                            if not education['major']:
                                                education['major'] = degree_major_part

                                # 如果成功提取到学校和学历/专业，添加到列表
                                if education['school'] and (education['degree'] or education['major']):
                                    education_list.append(education)
                                    pipe_format_handled = True  # 标记已处理
                                break  # 只处理第一个有效的entry

            # 如果已经处理了|格式，跳过后续处理
            if pipe_format_handled:
                i += 1
                continue

            # ========== 模式0: "专业 | 学历" 格式（优先检查，因为可能没有学校）==========
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    # 检查是否有学历关键词
                    has_degree = any(deu in parts[1] for deu in degree_keywords)
                    if has_degree:
                        education = {
                            'school': '',
                            'degree': '',
                            'major': '',
                            'duration': ''
                        }
                        education['major'] = parts[0].strip()
                        for degree in degree_keywords:
                            if degree in parts[1]:
                                education['degree'] = degree
                                break

                        # 向前搜索学校（范围：前5行）
                        if not education['school']:
                            for j in range(max(0, i - 5), i):
                                prev_line = lines[j].strip()
                                if '大学' in prev_line or '学院' in prev_line:
                                    education['school'] = prev_line
                                    break

                        # 向前搜索时间
                        if not education['duration']:
                            for j in range(max(0, i - 5), i):
                                prev_line = lines[j].strip()
                                time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', prev_line)
                                if time_match:
                                    education['duration'] = time_match.group(0)
                                    break

            # ========== 模式0b: "学校 / 学历" 格式（优先处理，因为包含"大学"会匹配模式1）==========
            # 例如："学历 :东北农业大学(211) / 本科" 或 "东北农业大学 / 本科"
            if '/' in line and ('大学' in line or '学院' in line) and not education:
                # 检查是否有学历关键词
                if any(deu in line for deu in degree_keywords):
                    parts = line.split('/')
                    if len(parts) >= 2:
                        # 第一部分是学校（可能包含"学历:"前缀）
                        school_part = parts[0].strip()
                        # 去掉"学历:"前缀
                        school_part = re.sub(r'^学历\s*[:：]\s*', '', school_part)
                        school_part = re.sub(r'^学校\s*[:：]\s*', '', school_part)

                        education = {
                            'school': school_part,
                            'degree': '',
                            'major': '',
                            'duration': ''
                        }

                        # 从第二部分提取学历
                        for degree in degree_keywords:
                            if degree in parts[1]:
                                education['degree'] = degree
                                break

            # ========== 新增模式: 处理"学校:xxx"格式（如乔亭志简历） ==========
            if '学校:' in line or 'school:' in line.lower():
                # 提取学校名
                school_match = re.search(r'学校[:：]\s*([^\s]+(?:[\u4e00-\u9fa5a-zA-Z\s]*大学|学院)?[\u4e00-\u9fa5a-zA-Z]*)', line)
                if school_match:
                    school_name = school_match.group(1).strip()
                    # 检查学校名是否有效（包含"大学"或"学院"）
                    if '大学' in school_name or '学院' in school_name:
                        education = {
                            'school': school_name,
                            'degree': '',
                            'major': '',
                            'duration': ''
                        }
                        # 向后搜索专业（通常在下一行或几行内）
                        for j in range(i + 1, min(i + 10, len(lines))):
                            next_line = lines[j].strip()
                            if not next_line:
                                continue
                            # 检查是否是专业行
                            if '专业:' in next_line or 'major:' in next_line.lower():
                                major_match = re.search(r'专业[:：]\s*([^\s]+.*)', next_line)
                                if major_match:
                                    education['major'] = major_match.group(1).strip()
                            # 如果遇到新的section，停止
                            if any(kw in next_line for kw in ['工作经历', '项目经验', '联系方式', '技能']):
                                break
                            # 如果找到专业了，停止搜索
                            if education['major']:
                                break

            # ========== 模式1: 学校名独立成行（包含"大学"或"学院"）==========
            if ('大学' in line or '学院' in line) and not education:
                # 跳过明显的内设学院（如"经济管理学院"、"外国语学院"等）
                # 这些通常是大学下属的学院，不是独立的学校
                skip_keywords = ['经济管理', '外国语', '人文', '理学', '工学', '法学', '医学',
                                '艺术', '体育', '信息', '软件', '计算机', '电气', '机械',
                                '土木', '化学', '材料', '生命', '环境', '建筑', '交通']
                # 跳过非学校的关键词（证书、英语等级、奖项等）
                # 检查是否包含英语等级相关关键词
                is_english_level = '英语' in line and ('级' in line or 'CET' in line)
                # 检查是否包含其他证书/奖项关键词
                is_certificate = any(kw in line for kw in ['证书', '荣誉', '奖项', '奖学金', '通过',
                                                           '普通话', '计算机二级', '二级', '四级', '六级'])
                # 检查是否是真正的大学（如"师范学院"、"财经大学"等）
                # 而不是内设学院（如"信息工程学院"）
                real_university_patterns = ['师范', '财经', '政法', '医药', '农业', '林业', '海洋',
                                           '民族', '体育', '艺术', '外语', '理工', '科技', '工业', '工商',
                                           '交通', '电力', '石油', '地质', '矿业', '冶金', '化工', '邮电',
                                           '中医药', '医科大学', '音乐学院', '美术学院']
                is_real_university = any(pattern in line for pattern in real_university_patterns)
                # 或者包含"大学"关键字
                has_university_keyword = '大学' in line

                # 只有包含"大学"或"学院"但不包含上述非学校关键词才处理
                should_skip = (
                    ('学院' in line and any(kw in line for kw in skip_keywords) and
                     not is_real_university and not has_university_keyword) or
                    is_english_level or is_certificate
                )

                if should_skip:
                    # 跳过非学校信息
                    pass
                else:
                    education = {
                        'school': line,  # 初始化为整行，后续会精细化提取
                        'degree': '',
                        'major': '',
                        'duration': ''
                    }

                    # ========== 优先级0: 检查"学校 • 内设学院 • 专业"格式（用•分隔）==========
                    # 例如：湖州师范学院 • 信息工程学院 • 计算机科学与技术 • GPA: 3.43
                    if ' • ' in line or ' · ' in line or ' | ' in line:
                        # 使用分隔符拆分
                        parts = re.split(r' [•·|] ', line)
                        if len(parts) >= 1:
                            # 第一部分通常是学校名
                            education['school'] = parts[0].strip()
                            # 查找专业（通常在第3部分或之后）
                            for i, part in enumerate(parts[1:], 1):
                                part = part.strip()
                                # 跳过GPA、Rank等非专业信息
                                if part.startswith('GPA') or part.startswith('Rank') or ':' in part:
                                    continue
                                # 检查是否看起来像专业名（2-10个汉字，不含"学院"等）
                                if '学院' not in part and len(part) >= 2 and len(part) <= 15:
                                    if re.match(r'^[\u4e00-\u9fa5（）()]+$|^[A-Za-z\s&/]+$', part):
                                        education['major'] = part
                                        break

                        # 向前搜索duration（因为时间通常在学校行之前）
                        if not education['duration']:
                            for j in range(i - 1, max(0, i - 5), -1):
                                prev_line = lines[j].strip()
                                if not prev_line:
                                    continue
                                # 检查是否包含时间格式
                                time_match = re.search(r'(\d{4})\s*[-.年—]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', prev_line)
                                if time_match:
                                    education['duration'] = time_match.group(0)
                                    break

                        # 如果找到了duration，尝试推断degree
                        if education['duration'] and not education['degree']:
                            year_match = re.findall(r'(\d{4})', education['duration'])
                            if len(year_match) == 2:
                                start_year, end_year = int(year_match[0]), int(year_match[1])
                                duration_years = end_year - start_year
                                if duration_years >= 3 and duration_years <= 5:
                                    education['degree'] = '本科'
                                elif duration_years >= 1 and duration_years <= 3:
                                    education['degree'] = '硕士'
                                elif duration_years >= 5:
                                    education['degree'] = '博士'

                    # ========== 优先级0.5: 处理非学历括号格式（如"国际商务(全英)"）==========
                    # 检查行中是否包含非学历括号
                    line_to_process = line
                    has_non_degree_paren = False
                    for non_degree in non_degree_parentheses:
                        # 检查中文或英文括号
                        if f'({non_degree})' in line or f'（{non_degree}）' in line:
                            has_non_degree_paren = True
                            # 移除这个非学历括号
                            line_to_process = line_to_process.replace(f'({non_degree})', '').replace(f'（{non_degree}）', '')
                            line_to_process = line_to_process.strip()

                    # 如果移除了非学历括号，重新解析这行
                    if has_non_degree_paren and line_to_process:
                        # 现在line_to_process应该像 "上海对外经贸大学 国际商务 2022.09-至今"
                        # 尝试提取时间（在行末）
                        time_match = re.search(r'(\d{4})\s*[-.年—]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', line_to_process)
                        if time_match:
                            education['duration'] = time_match.group(0)
                            # 移除时间后的部分
                            line_to_process = line_to_process[:time_match.start()].strip()

                        # 提取学校名（找到"大学"或"学院"关键字）
                        for uni_kw in ['大学', '学院', 'University', 'College']:
                            if uni_kw in line_to_process:
                                idx = line_to_process.index(uni_kw)
                                education['school'] = line_to_process[:idx + len(uni_kw)].strip()
                                # 剩余部分可能是专业
                                potential_major = line_to_process[idx + len(uni_kw):].strip()
                                if potential_major:
                                    education['major'] = potential_major
                                break

                        # 如果有duration但没有degree，推断学历
                        if education['duration'] and not education['degree']:
                            year_match = re.findall(r'(\d{4})', education['duration'])
                            # 处理"至今"情况
                            has_jinzhi = '至今' in education['duration'] or 'JinZhi' in education['duration'] or 'Present' in education['duration']

                            if len(year_match) >= 1:
                                start_year = int(year_match[0])
                                if has_jinzhi:
                                    # 使用当前年份作为结束年份
                                    from datetime import datetime
                                    end_year = datetime.now().year
                                elif len(year_match) >= 2:
                                    end_year = int(year_match[1])
                                else:
                                    end_year = None

                                if end_year:
                                    duration_years = end_year - start_year
                                    if duration_years >= 3 and duration_years <= 5:
                                        education['degree'] = '本科'
                                    elif duration_years >= 1 and duration_years <= 3:
                                        education['degree'] = '硕士'
                                    elif duration_years >= 5:
                                        education['degree'] = '博士'

                        # 如果推断出了degree，跳过后续的括号格式处理
                        if education['degree'] and education['school']:
                            # 跳过优先级1的处理
                            pass
                        else:
                            # 重置line以便后续处理
                            line_to_process = line

                    # ========== 优先级1: 检查"专业(学历)"括号格式（如"华东理工大学 专业催化(工学硕士)"）==========
                    # 如果优先级0.5已经成功提取了学校和学历，跳过此处理
                    if not (education['school'] and education['degree']):
                        # 使用正则提取括号中的学历（优先级最高，因为更精确）
                        for pattern in degree_patterns:
                            match = re.search(pattern, line)
                            if match:
                                education['degree'] = match.group(1)
                                # 提取括号前的部分（学校 + 专业）
                                # 使用正确的正则：匹配从左括号到右括号之间的内容
                                before_paren = re.sub(r'[()（）][^()（）]*', '', line).strip()
                                # 分离学校名和专业：找大学/学院关键字的位置
                                for uni_kw in ['大学', '学院', 'University', 'College']:
                                    if uni_kw in before_paren:
                                        idx = before_paren.index(uni_kw)
                                        # 检查大学关键字后面是否有内容（即专业）
                                        if idx + len(uni_kw) < len(before_paren):
                                            potential_major = before_paren[idx + len(uni_kw):].strip()
                                            # 如果后面的内容看起来像专业名（不含其他学校关键字）
                                            if potential_major and not any(kw in potential_major for kw in ['大学', '学院', 'University', 'College']):
                                                education['school'] = before_paren[:idx + len(uni_kw)].strip()
                                                education['major'] = potential_major
                                            else:
                                                education['school'] = before_paren.strip()
                                        else:
                                            education['school'] = before_paren.strip()
                                        break
                                if education['degree']:
                                    break

                    # ========== 优先级1.5: 检查横杠分隔格式（如"东北农业大学(211)-本科-物联网工程"）==========
                    # 只有在括号格式未提取到专业时才尝试
                    if not education['major'] and '-' in line:
                        parts = line.split('-')
                        if len(parts) >= 2:
                            # 第一部分是学校（可能包含标签如(211)）
                            school_part = parts[0].strip()
                            # 检查是否有大学/学院关键字
                            if '大学' in school_part or '学院' in school_part:
                                education['school'] = school_part

                                # 遍历剩余部分，查找学历和专业
                                for j in range(1, len(parts)):
                                    part = parts[j].strip()
                                    # 检查是否是学历
                                    if not education['degree']:
                                        for degree in degree_keywords:
                                            if degree in part:
                                                education['degree'] = degree
                                                # 如果这部分只包含学历，继续查找专业
                                                if part == degree:
                                                    continue
                                                break
                                    # 如果已找到学历，剩余的可能是专业
                                    if education['degree'] and not education['major']:
                                        # 去掉已识别的学历关键词，剩下的可能是专业
                                        major_part = part
                                        for degree in degree_keywords:
                                            if degree in major_part:
                                                major_part = major_part.replace(degree, '').strip()
                                                break
                                        # 如果还有内容且看起来像专业名（2-8个汉字或字母）
                                        if major_part and len(major_part) >= 2 and len(major_part) <= 15:
                                            # 排除一些明显不是专业的词
                                            exclude_words = {'时间', '年限', '至今', '奖学金', '证书', '荣誉', '项目'}
                                            if major_part not in exclude_words:
                                                education['major'] = major_part
                                                break

                    # ========== 优先级2: 检查普通"学历"关键词格式（如"学校 专业 学位 时间"）==========
                    # 只有在括号格式未匹配时才尝试
                    if not education['degree']:
                        for degree in degree_keywords:
                            if degree in line:
                                education['degree'] = degree
                                # 提取学校（去掉学位后的部分）
                                school_part = line.replace(degree, '').strip()
                                # 尝试提取时间（末尾的时间格式）
                                time_match = re.search(r'(\d{4})\s*[.-年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)(?:\s*[.-年]\s*\d{1,2})?', school_part)
                                if time_match:
                                    education['duration'] = time_match.group(0)
                                    # 去掉时间后的部分作为学校
                                    school_part = re.sub(time_match.group(0), '', school_part).strip()
                                # 尝试从剩余部分提取专业（如"学校 (英文名) 专业"格式）
                                if ')' in school_part or '）' in school_part:
                                    # 找到最后一个右括号
                                    last_paren_pos = max(school_part.rfind(')'), school_part.rfind('）'))
                                    if last_paren_pos > 0:
                                        potential_major = school_part[last_paren_pos + 1:].strip()
                                        # 如果括号后的内容看起来像专业名（2-6个汉字）
                                        if potential_major and re.match(r'^[\u4e00-\u9fa5]{2,6}$', potential_major):
                                            education['major'] = potential_major
                                            # 学校名是括号前的部分
                                            school_part = school_part[:last_paren_pos + 1].strip()
                                # 剩余部分作为学校名
                                education['school'] = school_part
                                break

                    # ========== 向前查找学历和专业（范围：前3行）- 支持时间->专业->学校格式 ==========
                    for j in range(max(0, i - 3), i):
                        prev_line = lines[j].strip()
                        if not prev_line:
                            continue

                        # 跳过明显的联系方式行（电话、邮箱等）
                        if any(kw in prev_line for kw in ['电话', '邮箱', '手机', 'TEL', 'Email', 'mail', '@', 'github.com', 'linkedin.com', ':155', ':186', ':138', ':139', ':137', ':136', ':135', ':188', ':189']):
                            continue  # 跳过联系方式行

                        # 跳过年龄、性别、CET等非专业信息行
                        if re.search(r'\d+\s*岁|^\d+\s*\||男|女|cet|CET|四级|六级|托福|雅思|GRE', prev_line):
                            continue  # 跳过年龄/性别/英语等级行

                        # 跳过明显不是专业的行（用continue继续向前搜索）
                        skip_prefixes = ['求职意向', '应聘', '意向', '岗位', '职位', '教育背景', '学习经历', '教育经历', '工作经历', '项目经验', '项目经历', '实习经历', '科研经历', '专业背景']
                        if any(prev_line.startswith(p) for p in skip_prefixes):
                            continue  # 跳过标题行，继续向前搜索
                        # 跳过看起来像姓名的短行（2-4个汉字，不包含常见专业关键词）
                        if re.match(r'^[\u4e00-\u9fa5]{2,4}$', prev_line):
                            # 常见专业关键词（如果包含这些词，可能是专业名而非姓名）
                            major_keywords = ['计算机', '软件', '电子', '机械', '会计', '金融', '经济', '管理', '化学', '物理', '数学', '生物', '医学', '文学', '历史', '哲学', '法学', '新闻', '艺术', '建筑', '土木', '电气', '自动化', '通信', '材料', '环境', '交通', '统计', '心理学']
                            if not any(kw in prev_line for kw in major_keywords):
                                continue  # 跳过姓名行

                        # 检查是否包含学历关键词
                        if not education['degree']:
                            for degree in degree_keywords:
                                if degree in prev_line:
                                    # 检查：如果这行只有学历关键词（没有其他内容），跳过
                                    # 因为这很可能是上一个学校的学历，不是当前学校的
                                    cleaned_line = prev_line.replace(degree, '').strip()
                                    if not cleaned_line:
                                        break  # 纯学历行，跳过
                                    # 有其他内容，提取学历和专业
                                    education['degree'] = degree
                                    # 提取专业（去掉学历后的部分）
                                    if cleaned_line and cleaned_line != '|' and not any(prev_line.startswith(p) for p in skip_prefixes):
                                        education['major'] = cleaned_line
                                    break

                        # 检查 "专业 | 学历" 格式
                        if not education['degree'] and '|' in prev_line:
                            parts = prev_line.split('|')
                            if len(parts) >= 2:
                                education['major'] = parts[0].strip()
                                for degree in degree_keywords:
                                    if degree in parts[1]:
                                        education['degree'] = degree
                                        break

                        # 如果还没有major且前一行看起来像专业名（纯中文2-6字）
                        if not education['major'] and len(prev_line) < 15:
                            if re.match(r'^[\u4e00-\u9fa5]{2,6}$', prev_line):
                                exclude_words = {'学校', '大学', '学历', '专业', '教育', '经历', '经验', '背景', '技能', '证书', '课程', '学习', '能力', '方向', '求职意向', '应聘', '项目', '实习', '科研'}
                                # 添加学历关键词到排除列表（避免"硕士"、"博士"被当作专业）
                                exclude_words.update(degree_keywords)
                                # 检查是否包含排除词（部分匹配）
                                if not any(excluded in prev_line for excluded in exclude_words):
                                    education['major'] = prev_line
                                # 如果学校名是之前的整行，更新为正确的学校名
                                break

                    # 向后查找学历和专业（范围：后20行，扩大搜索范围）
                    for j in range(i + 1, min(i + 21, len(lines))):
                        next_line = lines[j].strip()

                        # 空行跳过（继续向后搜索，不停止）
                        if not next_line:
                            continue

                        # ========== 优先检查：纯学历关键词行（如"本科"、"硕士"等）==========
                        # 这种格式常见于缩进的学历行，如："  本科"
                        if not education['degree'] and next_line in degree_keywords:
                            education['degree'] = next_line
                            continue  # 继续向后搜索专业和时间

                        # 检查行是否仅由学历关键词组成（可能前后有空格）
                        if not education['degree']:
                            for degree in degree_keywords:
                                if next_line == degree or next_line.strip() == degree:
                                    education['degree'] = degree
                                    break

                        # 跳过明显的非学历信息行
                        # 联系方式行特征：包含"电话"、"邮箱"、"手机"、"TEL"等关键字
                        if any(kw in next_line for kw in ['电话', '邮箱', '手机', 'TEL', 'Email', 'mail', '@', 'github.com', 'linkedin.com']):
                            continue
                        # 标题行特征：包含"求职意向"、"项目经验"等
                        if any(next_line.startswith(kw) or next_line == kw for kw in ['求职意向', '应聘', '项目经验', '项目经历', '工作经历', '实习经历', '技能', '荣誉', '奖项', '资格证书']):
                            break
                        # 过短的行，但如果包含学历关键词则不跳过（如"硕士"、"博士"）
                        if len(next_line) < 3:
                            # 检查是否是纯学历关键词
                            is_degree_keyword = next_line in degree_keywords
                            if not is_degree_keyword:
                                continue
                        # 遇到新学校停止（但不包括内设学院）
                        if '大学' in next_line:
                            break  # 遇到新大学，停止
                        # 跳过明显的内设学院（不停止搜索）
                        # 只有独立的学院名（短、不含学科关键词）才停止
                        if '学院' in next_line and len(next_line) < 15:
                            # 检查是否是内设学院（包含学科关键词）
                            internal_keywords = ['管理', '外国语', '人文', '理学', '工学', '法学', '医学',
                                                  '艺术', '体育', '信息', '软件', '计算机', '电气', '机械',
                                                  '土木', '化学', '材料', '生命', '环境', '建筑', '交通']
                            if not any(kw in next_line for kw in internal_keywords):
                                break  # 可能是独立的学院名

                        # 提取学历（优先查找包含"/"的行，如"会计 / 硕士"）
                        # 注意：后向搜索的degree应该覆盖前向搜索的degree（因为更近）
                        # 优先检查 "专业 / 学历" 格式
                        if not education['degree'] and '/' in next_line:
                            for degree in degree_keywords:
                                if degree in next_line:
                                    education['degree'] = degree
                                    # 同时提取专业（/前的部分）
                                    parts = next_line.split('/')
                                    if len(parts) > 0:
                                        education['major'] = parts[0].strip()
                                    break
                        # 检查括号格式，如 "软件工程(本科)" 或 "计算机科学与技术（硕士）"
                        if not education['degree']:
                            # 使用正则提取括号中的学历
                            for pattern in degree_patterns:
                                match = re.search(pattern, next_line)
                                if match:
                                    education['degree'] = match.group(1)
                                    # 提取专业（括号前的部分）
                                    major_part = re.sub(r'[()（）].*?', '', next_line).strip()
                                    if major_part:
                                        education['major'] = major_part
                                    break

                        # 检查行是否包含学历关键词（如"本科学历"、"本科在读"等）
                        if not education['degree']:
                            for degree in degree_keywords:
                                if degree in next_line:
                                    education['degree'] = degree
                                    break

                        # 如果已找到学历和专业，停止向后搜索
                        if education['degree'] and education['major']:
                            break

                        # 如果没有major，尝试从独立的专业名称行提取
                        if not education['major'] and len(next_line) < 15:
                            # 跳过包含"学院"的行（那是内设学院，不是专业）
                            if '学院' not in next_line:
                                # 检查是否是纯中文专业名称（2-6个汉字，无特殊字符）
                                if re.match(r'^[\u4e00-\u9fa5]{2,6}$', next_line):
                                    # 排除一些明显不是专业的词
                                    exclude_words = {'学校', '大学', '学历', '专业', '教育', '经历', '经验', '背景', '技能', '证书', '课程', '学习', '能力', '方向'}
                                    # 添加学历关键词到排除列表（避免"硕士"、"博士"被当作专业）
                                    exclude_words.update(degree_keywords)
                                    if next_line not in exclude_words:
                                        education['major'] = next_line

                        # 提取时间
                        if not education['duration']:
                            # 标准格式：2019.06-2023.06 或 2019年06月-2023年06月
                            time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', next_line)
                            if time_match:
                                education['duration'] = time_match.group(0)
                                # 如果行中包含时间，尝试提取时间前的专业（如"产业经济学 2023.09-2026.06"）
                                if not education['major']:
                                    before_time = next_line[:time_match.start()].strip()
                                    # 移除常见的分隔符
                                    before_time = re.sub(r'[\s、，,]+$', '', before_time).strip()
                                    # 检查是否是有效的专业名（2-15个字符，可能是中文或含括号/斜杠）
                                    if before_time and 2 <= len(before_time) <= 15 and re.match(r'^[\u4e00-\u9fa5()（）/\-·]+$', before_time):
                                        # 排除明显不是专业的词
                                        exclude_words = {'学校', '大学', '学历', '专业', '教育', '经历', '经验', '背景', '技能', '证书', '课程', '学习', '能力', '方向'}
                                        if not any(excluded in before_time for excluded in exclude_words):
                                            education['major'] = before_time
                            # 特殊格式：2019 年 6 月至 2023 年 6 月（带空格和"至"）
                            elif not education['duration']:
                                time_match = re.search(r'(\d{4})\s*年\s*\d{1,2}\s*月\s*[-.年—至到]+\s*(\d{4}|\d{1,2}|至今)', next_line)
                                if time_match:
                                    education['duration'] = time_match.group(0)

                    # 向前查找时间（范围：前2行）
                    if not education['duration']:
                        for j in range(max(0, i - 2), i):
                            prev_line = lines[j].strip()
                            time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', prev_line)
                            if time_match:
                                education['duration'] = time_match.group(0)
                                break

            # ========== 模式2: 同一行包含"学校 / 学历"格式 ==========
            # 例如："学历 :东北农业大学(211) / 本科" 或 "东北农业大学 / 本科"
            elif '/' in line and ('大学' in line or '学院' in line):
                # 检查是否有学历关键词
                if any(deu in line for deu in degree_keywords):
                    parts = line.split('/')
                    if len(parts) >= 2:
                        # 第一部分是学校（可能包含"学历:"前缀）
                        school_part = parts[0].strip()
                        # 去掉"学历:"前缀
                        school_part = re.sub(r'^学历\s*[:：]\s*', '', school_part)
                        school_part = re.sub(r'^学校\s*[:：]\s*', '', school_part)

                        education = {
                            'school': school_part,
                            'degree': '',
                            'major': '',
                            'duration': ''
                        }

                        # 从第二部分提取学历
                        for degree in degree_keywords:
                            if degree in parts[1]:
                                education['degree'] = degree
                                break

            # ========== 模式3: 同一行包含学校+学历（空格分隔，如"上海大学 本科"）==========
            elif any(edu in line for edu in degree_keywords) and ('大学' in line or '学院' in line):
                education = {
                    'school': '',
                    'degree': '',
                    'major': '',
                    'duration': ''
                }

                # 提取学历
                for degree in degree_keywords:
                    if degree in line:
                        education['degree'] = degree
                        # 提取学校（去掉学历后的部分）
                        school_part = line.replace(degree, '').strip()
                        education['school'] = school_part
                        break

            # ========== 模式4: 独立的"学历 时间"格式（如"研究生 2023.09 - 2026.07"）==========
            # 这种格式通常出现在学校行之后，用于描述该学校的学历层次
            # 需要与前面的学校记录关联
            if not education and any(degree in line for degree in degree_keywords):
                # 检查是否包含时间
                time_match = re.search(r'(\d{4})\s*[-./年—]\s*\d{1,2}\s*[-./年—至到]\s*(\d{4}|\d{1,2}|至今)', line)
                if time_match:
                    # 提取学历
                    for degree in degree_keywords:
                        if degree in line:
                            # 映射"研究生"为更具体的学历（硕士/博士）
                            mapped_degree = degree
                            if degree == '研究生':
                                # 根据时间长度判断是硕士还是博士
                                duration_years = 0
                                year_match = re.findall(r'(\d{4})', time_match.group(0))
                                if len(year_match) >= 2:
                                    start_year, end_year = int(year_match[0]), int(year_match[1])
                                    duration_years = end_year - start_year
                                # 1-3年通常是硕士，3年以上是博士
                                if duration_years >= 1 and duration_years <= 3:
                                    mapped_degree = '硕士'
                                elif duration_years > 3:
                                    mapped_degree = '博士'
                                else:
                                    mapped_degree = '硕士'  # 默认硕士

                            # 查找前一个最近的学校记录
                            if education_list:
                                # 将学历和时间关联到前一个学校记录
                                prev_edu = education_list[-1]
                                if not prev_edu.get('degree'):
                                    prev_edu['degree'] = mapped_degree
                                if not prev_edu.get('duration'):
                                    prev_edu['duration'] = time_match.group(0)
                                break
                            else:
                                # 没有前面的学校记录，创建一个新的记录（学校为空）
                                education = {
                                    'school': '',
                                    'degree': mapped_degree,
                                    'major': '',
                                    'duration': time_match.group(0)
                                }
                                education_list.append(education)
                            break

            # 如果找到学校但没有学历，尝试推断
            if education and education['school'] and not education['degree']:
                # 检查时间范围推断学历
                if education['duration']:
                    year_match = re.findall(r'(\d{4})', education['duration'])
                    if len(year_match) == 2:
                        start_year, end_year = int(year_match[0]), int(year_match[1])
                        duration_years = end_year - start_year
                        if duration_years >= 3 and duration_years <= 5:
                            education['degree'] = '本科'
                        elif duration_years >= 1 and duration_years <= 3:
                            education['degree'] = '硕士'

            # 添加到列表（只要有学校，或有专业+学历即可）
            if education and (education['school'] or (education['degree'] and education['major'])):
                # 检查是否已存在相同school的记录，避免重复
                is_duplicate = False
                if education['school']:
                    for existing in education_list:
                        if existing.get('school') == education['school']:
                            is_duplicate = True
                            break
                if is_duplicate:
                    i += 1
                    continue
                # 如果学校名为空但有degree和major，标记school为未知
                if not education['school'] and education['degree'] and education['major']:
                    education['school'] = '未知'
                education_list.append(education)

                # 最多取5条
                if len(education_list) >= 5:
                    break

            i += 1

        # ========== 全文搜索模式：如果上面的方法没找到任何教育经历，则从全文中搜索 ==========
        if not education_list:
            # 在全文中查找包含学校名称的行
            for i, line in enumerate(lines):
                line = line.strip()
                # 查找包含"大学"或"学院"的行
                if ('大学' in line or '学院' in line) and len(line) < 50:  # 避免匹配到过长的文本
                    # 向后搜索10行，查找学历信息
                    education = {
                        'school': line,
                        'degree': '',
                        'major': '',
                        'duration': ''
                    }

                    # 向前查找时间（范围：前2行）
                    for j in range(max(0, i - 2), i):
                        prev_line = lines[j].strip()
                        time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', prev_line)
                        if time_match:
                            education['duration'] = time_match.group(0)
                            break

                    # 向后查找学历和专业（范围：后10行）
                    for j in range(i + 1, min(i + 11, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            break
                        if '大学' in next_line or '学院' in next_line:
                            break

                        # 使用正则提取括号中的学历
                        if not education['degree']:
                            for pattern in degree_patterns:
                                match = re.search(pattern, next_line)
                                if match:
                                    education['degree'] = match.group(1)
                                    # 提取专业（括号前的部分）
                                    major_part = re.sub(r'[()（）].*?', '', next_line).strip()
                                    education['major'] = major_part
                                    break

                            # 如果没找到括号格式，尝试普通查找
                            if not education['degree']:
                                for degree in degree_keywords:
                                    if degree in next_line:
                                        education['degree'] = degree
                                        break

                        # 提取时间
                        if not education['duration']:
                            # 标准格式：2019.06-2023.06 或 2019年06月-2023年06月
                            time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', next_line)
                            if time_match:
                                education['duration'] = time_match.group(0)
                            # 特殊格式：2019 年 6 月至 2023 年 6 月（带空格和"至"）
                            elif not education['duration']:
                                time_match = re.search(r'(\d{4})\s*年\s*\d{1,2}\s*月\s*[-.年—至到]+\s*(\d{4}|\d{1,2}|至今)', next_line)
                                if time_match:
                                    education['duration'] = time_match.group(0)

                    # 如果找到了学校但没有学历，尝试推断
                    if education['school'] and not education['degree']:
                        # 检查时间范围：如果是4年制（如2018.08-2022.07），推断为本科
                        if education['duration']:
                            year_match = re.findall(r'(\d{4})', education['duration'])
                            if len(year_match) == 2:
                                start_year, end_year = int(year_match[0]), int(year_match[1])
                                duration = end_year - start_year
                                if duration >= 3 and duration <= 5:
                                    education['degree'] = '本科'
                                elif duration >= 1 and duration <= 3:
                                    education['degree'] = '硕士'

                    # 如果找到了学历或学校，添加到列表
                    if education['school'] or education['degree']:
                        education_list.append(education)

                        # 最多取3条
                        if len(education_list) >= 3:
                            break

        # 后处理：从school字段中提取degree并清理school名称
        education_list = EducationExtractor._post_process_education(education_list)
        return education_list

    @staticmethod
    def _post_process_education(education_list: List[Dict]) -> List[Dict]:
        """后处理教育经历列表，从school字段中提取degree并清理school名称"""
        degree_keywords = ['博士', '硕士', '本科', '大专', '高中', '专升本', '中专', 'MBA', 'EMBA']

        for education in education_list:
            # 映射"研究生"为更具体的学历（硕士/博士）
            if education.get('degree') == '研究生':
                # 根据时间长度判断
                duration = education.get('duration', '')
                if duration:
                    year_match = re.findall(r'(\d{4})', duration)
                    if len(year_match) >= 2:
                        start_year, end_year = int(year_match[0]), int(year_match[1])
                        duration_years = end_year - start_year
                        # 1-3年通常是硕士，3年以上是博士
                        if duration_years >= 1 and duration_years <= 3:
                            education['degree'] = '硕士'
                        elif duration_years > 3:
                            education['degree'] = '博士'
                        else:
                            education['degree'] = '硕士'  # 默认硕士
                else:
                    # 没有时间信息，默认硕士
                    education['degree'] = '硕士'
            # ========== 优先处理：清理学校名称（移除时间前缀、英文括号等）==========
            if education.get('school'):
                school = education['school']

                # 1. 移除时间前缀（如 "2024-09 ~ 2025-12 "、"2020.09-2024.06 "）
                # 支持多种时间格式：
                # - 2024-09 ~ 2025-12
                # - 2024.09-2024.12
                # - 2024年09月-2024年12月
                # - 2024.09 - 2025.12
                school = re.sub(r'^[\d\s\-\.~—年月日至今至到]+', '', school).strip()

                # 2. 移除英文括号内容（如 "(Columbia University)"、"（Columbia University）"）
                # 但保留中文括号内容（可能包含专业信息）
                school = re.sub(r'\([A-Za-z\s\.]+\)', '', school).strip()
                school = re.sub('（[A-Za-z\s\.]+）', '', school).strip()

                # 3. 移除学校名末尾的时间后缀（如 "哥伦比亚大学 2024-09 ~ 2025-12"）
                school = re.sub(r'[\s\-\.~—年月日至今至toTO]+\d+[\s\-\.~—年月日至今至toTO]*\d*[\s\-\.~—年月日至今至toTO]*$', '', school).strip()

                # 4. 移除末尾的GPA、Rank、专业等信息（多种分隔符）
                # 处理格式：
                # - "哥伦比���大学 科技与传媒GPA: 4.0" -> "哥伦比亚大学"
                # - "美国哥伦比亚大学 |应用分析" -> "哥伦比亚大学"
                # - "湖州师范学院 • 信息工程学院" -> "湖州师范学院"
                # - "哥伦比亚大学(211)" -> "哥伦比亚大学" (括号在后续处理)
                separators = [' • ', ' |', ' | ', ' · ', '  ', '\t', '（', '(']

                # 找到第一个分隔符的位置
                first_sep_pos = -1
                first_sep = None
                for sep in separators:
                    pos = school.find(sep)
                    if pos != -1 and (first_sep_pos == -1 or pos < first_sep_pos):
                        first_sep_pos = pos
                        first_sep = sep

                # 如果找到分隔符，智能选择学校名部分
                if first_sep_pos > 0 and first_sep:
                    before_sep = school[:first_sep_pos].strip()
                    after_sep = school[first_sep_pos + len(first_sep):].strip()

                    # 策略：优先选择包含"大学"或"学院"的部分
                    before_has_uni = '大学' in before_sep or '学院' in before_sep
                    after_has_uni = '大学' in after_sep or '学院' in after_sep

                    if after_has_uni and not before_has_uni:
                        # 分隔符后的部分才是学校名（如 "International Finance | 格拉斯哥大学"）
                        school = after_sep
                    elif before_has_uni and not after_has_uni:
                        # 分隔符前的部分是学校名（如 "哥伦比亚大学 |应用分析"）
                        school = before_sep
                    elif after_has_uni and before_has_uni:
                        # 两边都有，优先选择后面的（通常更准确）
                        school = after_sep
                    else:
                        # 两边都没有，保留前面的
                        school = before_sep

                # 5. 移除GPA、Rank等常见后缀（如果在没有分隔符的情况下）
                # 例如: "哥伦比亚大学 科技与传媒GPA: 4.0" 已经被上面处理
                # 这里处理格式如 "哥伦比亚大学GPA:4.0" 或 "某某大学Rank:10"
                school = re.sub(r'\s*(GPA|Rank|排名|成绩|绩点).*$', '', school, flags=re.IGNORECASE).strip()

                # 5.5 移除学校名后的专业描述（通常是2-10个汉字后跟GPA/括号等）
                # 例如: "哥伦比亚大学 科技与传媒GPA" -> "哥伦比亚大学"
                # 策略：找到大学/学院关键字，只保留到关键字的部分
                if '大学' in school or '学院' in school:
                    # 找到大学/学院关键字的位置
                    for keyword in ['大学', '学院']:
                        if keyword in school:
                            idx = school.index(keyword)
                            # 提取学校名（到关键字结束）
                            potential_school = school[:idx + len(keyword)]
                            # 检查后面是否有空格跟着中文（可能是专业名）
                            remaining_raw = school[idx + len(keyword):]
                            if remaining_raw and remaining_raw[0] in ' 	':
                                remaining = remaining_raw.strip()
                                # 如果剩余部分主要是中文且不含数字/GPA等，可能是专业名
                                if re.match(r'^[\u4e00-\u9fa5]{2,15}$', remaining) or \
                                   re.match(r'^[\u4e00-\u9fa5]{2,15}\s+(GPA|Rank|QS|TOP)', remaining):
                                    school = potential_school
                                    break

                # 6. 移除中文括号中的标签（如 "(211)" "(985)" "(双一流)" 等）
                # 但保留专业信息括号（如 "（计算机科学与技术）"）
                # 判断逻辑：如果括号内容短且是标签词，移除
                tag_patterns = [
                    r'\(211\)', r'（211）',
                    r'\(985\)', r'（985）',
                    r'\(双一流\)', r'（双一流）',
                    r'\(双非\)', r'（双非）',
                    r'\(QS[:：]?前?\d*\)', r'（QS[:：]?前?\d*）',  # QS排名标签
                    r'\(TOP?\d*\)', r'（TOP?\d*）',  # TOP排名标签
                ]
                for tag_pattern in tag_patterns:
                    school = re.sub(tag_pattern, '', school).strip()

                # 6.5 移除QS、TOP等排名标签（无括号格式）
                # 例如: "英属哥伦比亚大学 QS:前 50" -> "英属哥伦比亚大学"
                # "某某大学 TOP100" -> "某某大学"
                rank_patterns = [
                    r'\s+QS[:：]?\s*前?\s*\d*',
                    r'\s+TOP?\s*\d*',
                    r'\s+排名[:：]?\s*\d*',
                ]
                for rank_pattern in rank_patterns:
                    school = re.sub(rank_pattern, '', school).strip()

                # 7. 移除"美国"、"英国"等国家前缀（保留"中国"因为需要区分港澳台）
                # 例如: "美国哥伦比亚大学" -> "哥伦比亚大学"
                # 但保留 "中国人民大学" "中国传媒大学" "英属哥伦比亚大学" 等
                country_prefixes = ['美国', '英国', '加拿大', '澳大利亚', '日本', '韩国', '德国', '法国',
                                   '新加坡', '马来西亚', '意大利', '西班牙', '瑞士', '荷兰', '瑞典']
                for prefix in country_prefixes:
                    if school.startswith(prefix):
                        # 检查后面是否跟着大学/学院（关键字在末尾而非开头）
                        remaining = school[len(prefix):].strip()
                        # 检查remaining是否以"大学"或"学院"结尾
                        if remaining.endswith('大学') or remaining.endswith('学院'):
                            school = remaining
                            break

                education['school'] = school
            # 如果degree为空但school不为空，尝试从school中提取degree
            if not education.get('degree') and education.get('school'):
                school = education['school']

                # 检查school中是否包含degree关键词
                for degree in degree_keywords:
                    if degree in school:
                        education['degree'] = degree
                        # 清理school名称：移除degree关键词
                        # 处理各种格式：
                        # - "中北大学本科财务管理" -> "中北大学财务管理"
                        # - "复旦大学硕士工商管理" -> "复旦大学工商管理"
                        # - "本科学历 湖州师范学院" -> "湖州师范学院"

                        # 先尝试找到degree的位置
                        idx = school.find(degree)
                        if idx >= 0:
                            # 移除degree关键词
                            cleaned_school = school[:idx] + school[idx + len(degree):]
                            # 清理可能的分隔符和多余空格
                            cleaned_school = cleaned_school.strip(' ·•-—–\t ')
                            # 清理"学历"前缀（如"学历 湖州师范学院" -> "湖州师范学院"）
                            cleaned_school = re.sub(r'^学历\s*[:：]?\s*', '', cleaned_school)
                            cleaned_school = cleaned_school.strip()
                            education['school'] = cleaned_school if cleaned_school else school[:idx]
                        break

            # 清理school字段中明显的错误识别
            # 例如："奖项荣誉"被识别为学校
            if education.get('school'):
                school = education['school']
                # 过滤明显的非学校名称
                non_school_keywords = ['奖项荣誉', '荣誉奖项', '获奖情况', '奖励', '证书',
                                      '奖学金', '通过', '获得', '等级', '考试', '成绩',
                                      '英语等级', 'CET', '雅思', '托福', 'GRE', '学历 ',
                                      '四级', '六级', 'CET-4', 'CET-6', '大学英语']
                if any(kw in school for kw in non_school_keywords):
                    # 如果包含这些关键词，清空school（这不是有效的学校信息）
                    education['school'] = ''
                # 检查school是否以"学历"开头（无效）
                if school.startswith('学历') or school.startswith('学历:'):
                    education['school'] = ''

        return education_list
