"""简历解析服务 - 支持PDF和DOCX格式"""
import re
import jieba
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ResumeParser:
    """简历解析器"""

    def __init__(self):
        """初始化简历解析器"""
        # 设置jieba分词
        jieba.setLogLevel(jieba.logging.INFO)

    def parse_resume(self, file_path: str, email_subject: Optional[str] = None) -> Dict:
        """解���简历文件

        Args:
            file_path: 简历文件路径

        Returns:
            解析后的简历信息
        """
        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == '.pdf':
                return self._parse_pdf(file_path, email_subject=email_subject)
            elif file_ext in ['.docx', '.doc']:
                return self._parse_docx(file_path, email_subject=email_subject)
            else:
                logger.error(f"不支持的文件格式: {file_ext}")
                return {}

        except Exception as e:
            logger.error(f"解析简历失败: {e}")
            return {}

    def _parse_pdf(self, file_path: str, email_subject: Optional[str] = None) -> Dict:
        """解析PDF简历 - 增强版（PyMuPDF主 + pdfplumber备）"""
        from app.utils.text_cleaner import TextCleaner

        # 策略1: PyMuPDF (主要) - 更好的中文支持
        try:
            import fitz  # PyMuPDF
            logger.info(f"使用PyMuPDF解析PDF: {file_path}")

            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    # 提取文本（使用"text"模式，适合文本型PDF）
                    page_text = page.get_text("text")
                    text += page_text + "\n"

            # 清理文本
            text = TextCleaner.clean_text(text)
            logger.info(f"PyMuPDF解析完成，文本长度: {len(text)} 字符")

            return self._parse_text(text, email_subject=email_subject, filename=file_path)

        except ImportError:
            logger.warning("PyMuPDF未安装，使用pdfplumber作为fallback")

        # 策略2: pdfplumber (fallback)
        try:
            import pdfplumber
            logger.info(f"使用pdfplumber解析PDF: {file_path}")

            with pdfplumber.open(file_path) as pdf:
                # 提取所有文本
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""

            # 清理文本
            text = TextCleaner.clean_text(text)
            logger.info(f"pdfplumber解析完成，文本长度: {len(text)} 字符")

            return self._parse_text(text, email_subject=email_subject, filename=file_path)

        except ImportError:
            logger.error("PDF解析库未安装（PyMuPDF和pdfplumber都不可用）")
            return {}
        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            return {}

    def _parse_docx(self, file_path: str, email_subject: Optional[str] = None) -> Dict:
        """解析DOCX简历"""
        try:
            from docx import Document

            doc = Document(file_path)

            # 提取所有文本
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"

            # 解析文本
            return self._parse_text(text, email_subject=email_subject, filename=file_path)

        except ImportError:
            logger.error("python-docx未安装，无法解析DOCX")
            return {}
        except Exception as e:
            logger.error(f"解析DOCX失败: {e}")
            return {}

    def _parse_text(self, text: str, email_subject: Optional[str] = None, filename: Optional[str] = None) -> Dict:
        """解析简历文本

        Args:
            text: 简历文本
            email_subject: 邮件标题（可选，用于优先提取姓名）
            filename: 文件名（可选，用于从文件名提取姓名）

        Returns:
            解析后的简历信息
        """
        result = {
            'candidate_name': None,
            'phone': None,
            'email': None,
            'education': None,
            'work_years': None,
            'skills': [],
            'work_experience': [],
            'project_experience': [],
            'education_history': [],
            'raw_text': text
        }

        # 提取基本信息
        result['phone'] = self._extract_phone(text)
        result['email'] = self._extract_email(text)

        # 优先级1: 从邮件标题提取姓名
        if email_subject:
            result['candidate_name'] = self._extract_name_from_email_subject(email_subject)
            if result['candidate_name']:
                logger.info(f"从邮件主题提取姓名: {result['candidate_name']}")

        # 优先级2: 从文件名提取姓名
        if not result['candidate_name'] and filename:
            result['candidate_name'] = self._extract_name_from_filename(filename)
            if result['candidate_name']:
                logger.info(f"从文件名提取姓名: {result['candidate_name']}")

        # 优先级3: 从简历正文提取姓名
        if not result['candidate_name']:
            result['candidate_name'] = self._extract_name(text)
            if result['candidate_name']:
                logger.info(f"从简历正文提取姓名: {result['candidate_name']}")

        # 提取教育背景
        result['education_history'] = self._extract_education(text)
        if result['education_history']:
            # 取最高学历
            education_order = ['博士', '硕士', '本科', '大专', '高中']
            highest_edu_record = None
            for edu in education_order:
                for edu_history in result['education_history']:
                    if edu in edu_history.get('degree', ''):
                        result['education'] = edu
                        highest_edu_record = edu_history
                        break
                if result['education']:
                    break

            # 判断最高学历的学校类型
            if highest_edu_record and highest_edu_record.get('school'):
                from app.services.school_classifier import get_school_classifier
                classifier = get_school_classifier()
                school_name = highest_edu_record.get('school', '')
                result['education_level'] = classifier.classify(school_name)
                logger.info(f"学历：{result['education']}，学校：{school_name}，等级：{result.get('education_level', '未知')}")

        # 提取工作经历
        result['work_experience'] = self._extract_work_experience(text)

        # 计算工作年限
        if result['work_experience']:
            result['work_years'] = self._calculate_work_years(result['work_experience'])

        # 提取项目经历
        result['project_experience'] = self._extract_project_experience(text)

        # 提取技能关键词（带熟练度检测）
        skills_with_levels = self._extract_skills_with_proficiency(text)
        result['skills'] = (
            skills_with_levels['expert'] +
            skills_with_levels['proficient'] +
            skills_with_levels['familiar'] +
            skills_with_levels['mentioned']
        )
        result['skills_by_level'] = skills_with_levels  # 存储供后续使用

        return result

    def _extract_phone(self, text: str) -> Optional[str]:
        """提取手机号 - 支持多种格式

        支持格式：
        1. 13800138000（连续11位）
        2. 158 0066 4286（带空格）
        3. 139 1234 5678（带空格）
        4. 021-12345678（座机）
        """
        # 预处理：移除所有空格，以便匹配带空格的手机号
        text_no_spaces = text.replace(' ', '').replace('　', '')  # 包括中文空格

        # 匹配手机号格式
        patterns = [
            r'1[3-9]\d{9}',  # 11位手机号（从去空格后的文本中匹配）
            r'\d{3,4}-\d{7,8}',  # 座机号（原格式）
        ]

        # 优先从去空格的文本中匹配手机号
        match = re.search(patterns[0], text_no_spaces)
        if match:
            return match.group()

        # 匹配座机号（从原文）
        match = re.search(patterns[1], text)
        if match:
            return match.group()

        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """提取邮箱"""
        # 匹配邮箱格式
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, text)

        if match:
            return match.group()

        return None

    def _extract_name(self, text: str) -> Optional[str]:
        """提取姓名 - 改进版"""
        lines = text.strip().split('\n')

        # 黑名单词（这些词看起来像姓名但不是）
        blacklist = {
            # 标题类
            '教育背景', '基本信息', '个人优势', '工作经历', '项目经验',
            '求职意向', '教育经历', '专业技能', '自我评价', '联系方式',
            '个人简历', '简历', '姓名', '名字', '候选人', '应聘',
            # 信息字段
            '男', '女', '年龄', '电话', '邮箱', '邮箱', '地址', '籍贯',
            '学历', '学位', '专业', '学校', '毕业', '院校',
            # 学历
            '本科', '硕士', '博士', '大专', '专科', '高中', '中专',
            '专升本', '研究生', '本科生', '硕士生', '博士生',
            # 职位/岗位相关
            '总账会计', '财务专员', '销售总监', '软件工程师', '产品经理',
            '项目经历', '实习经历', '工作内容', '主要职责',
            # 专业/学科
            '软件工程', '电子信息', '计算机科学', '通信工程', '机械工程',
            '数据科学', '人工智能', '自动化', '电气工程',
            # 其他常见非姓名词汇
            '个人介绍', '基本信息', '专业技能', '主修课程', '获奖情况',
            '证书情况', '语言能力', '计算机能力', '工作内容',
        }

        # 模式1: 查找明确的"姓名：xxx"或"名字：xxx"格式
        for line in lines[:20]:
            line = line.strip()
            # 匹配 "姓名：张三" 或 "名字：张三" 或 "候选人：张三"
            match = re.search(r'姓\s*名\s*[:：]\s*([^\s|]{2,4})', line)
            if match:
                name = match.group(1).strip()
                if self._is_valid_name(name, blacklist):
                    return name

            # 匹配 "Name: 张三"
            match = re.search(r'[Nn]ame\s*[:：]\s*([^\s|]{2,4})', line)
            if match:
                name = match.group(1).strip()
                if self._is_valid_name(name, blacklist):
                    return name

        # 模式2: 查找独立成行的姓名（2-4个汉字）
        for line in lines[:20]:
            line = line.strip()
            # 跳过太长的行
            if len(line) > 15:
                continue
            # 跳过包含特殊字符的行（但不包括空格、冒号、竖线）
            if re.search(r'[0-9@\.]', line):
                continue
            # 匹配纯中文姓名（2-4个汉字）
            match = re.search(r'^([\u4e00-\u9fa5]{2,4})$', line)
            if match:
                name = match.group(1).strip()
                if self._is_valid_name(name, blacklist):
                    return name

        # 模式3: 从格式化的行中提取（如 "张三 | 男 | 25岁"）
        for line in lines[:20]:
            line = line.strip()
            # 匹配 "张三|男|25" 或 "张三 | 男 | 25"
            parts = re.split(r'\s*[|｜]\s*', line)
            for part in parts:
                part = part.strip()
                # 第一个部分通常是姓名
                if re.match(r'^[\u4e00-\u9fa5]{2,4}$', part):
                    name = part
                    if self._is_valid_name(name, blacklist):
                        return name
                    break  # 只检查第一个部分

        return None

    def _is_valid_name(self, name: str, blacklist: set) -> bool:
        """判断是否为有效的姓名"""
        if not name:
            return False

        # 检查是否在黑名单中
        if name in blacklist:
            return False

        # 检查是否包含非中文字符
        if not re.match(r'^[\u4e00-\u9fa5]+$', name):
            return False

        # 检查长度（姓名通常是2-4个字）
        if len(name) < 2 or len(name) > 4:
            return False

        # 检查是否包含明显的非姓名词汇（这些词通常不会单独出现作为姓名）
        invalid_suffixes = [
            '工程师', '专员', '总监', '经理', '助理', '顾问',
            '经历', '经验', '内容', '职责', '情况', '能力',
            '简历', '应聘', '招聘', '岗位', '职位', '公司',
            '专业', '工程', '科学', '技术', '管理', '经济',
        ]
        for suffix in invalid_suffixes:
            if name.endswith(suffix) or name.startswith(suffix):
                return False

        # 姓氏检查（常见标题字，帮助过滤一些明显不是姓名的词）
        # 如果名字以这些常见标题字开头，可能不是姓名
        invalid_prefixes = ['总', '主', '项', '实', '个', '教', '工', '学']
        if name[0] in invalid_prefixes and len(name) >= 3:
            # 检查是否可能是个标题（3-4个字且以特定字开头）
            if len(name) == 3:
                # 3个字的标题词
                for bad_name in ['总账会计', '项目经历', '实习经历', '工作经历',
                                '个人优势', '基本信息', '教育背景']:
                    if name == bad_name:
                        return False
            if len(name) == 4:
                # 4个字的词可能是标题，不是姓名
                for suffix in ['经历', '情况', '能力', '技能', '背景', '内容', '职责']:
                    if name.endswith(suffix):
                        return False

        return True

    def _extract_name_from_email_subject(self, subject: str) -> Optional[str]:
        """从邮件标题中提取姓名

        常见格式（80%是职位-姓名格式）：
        - "产品经理助理-郭子义-西交利物浦大学" （职位-姓名-学校）
        - "Java开发工程师-王明-上海" （职位-姓名-地点）
        - "财务信息化顾问-李景-澳门科技大学" （职位-姓名-学校）
        - "张三 | 10年以上，应聘 销售总监 | 上海40-70K【BOSS直聘】" （姓名在前）
        """
        if not subject:
            return None

        # 黑名单词
        blacklist = {
            '同学', '先生', '女士', '求职者', '候选人', '应届生',
            '开发', '工程师', '设计师', '实施', '顾问',
        }

        # ========== 模式1: "职位-姓名-其他"��最常见，80%的情况）==========
        # 匹配：职位 - 姓名 - 其他
        # 例如："产品经理助理-郭子义-西交利物浦大学"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})(?:-|$)', subject)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式1b: "职位-姓名（备注）-其他" 或 "职位-姓名（备注）"（新增）==========
        # 匹配：职位 - 姓名(备注) - 其他 或 职位 - 姓名(备注)
        # 例如："财务信息化顾问-李景昱（中）.pdf"、"产品经理-张三（男）"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})(?:（[^）]*）)?(?:-|$|\.|\s)', subject)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式2: "姓名 | 其他信息"（姓名在最前面）==========
        # 例如："张三 | 10年以上，应聘 销售总监 | 上海40-70K"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})\s*\|', subject)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式3: "姓名|其他信息"（没有空格的竖线分隔）==========
        # 例如："张三|应聘销售总监"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})\|', subject)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式4: "【岗位】姓名_其他信息" ==========
        # 例如："【销售总监】张三_简历"
        match = re.search(r'【[^】]*】\s*([\u4e00-\u9fa5]{2,4})_', subject)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式5: 尝试从竖线分隔的第一部分提取 ==========
        # 例如："张三 | 10年以上 | 应聘岗位"
        parts = re.split(r'\s*[|｜]\s*', subject)
        if len(parts) > 0:
            first_part = parts[0].strip()
            # 第一个部分是纯2-4个汉字
            if re.match(r'^[\u4e00-\u9fa5]{2,4}$', first_part):
                name = first_part
                if self._is_valid_name(name, blacklist):
                    return name

        return None

    def _extract_name_from_filename(self, filename: str) -> Optional[str]:
        """从文件名中提取姓名

        常见格式:
        - "财务信息化顾问-李景昱（中）.pdf"
        - "20250130_123456_职位-姓名（备注）.pdf"
        - "产品经理-张三.pdf"
        """
        if not filename:
            return None

        # 提取纯文件名（去掉路径和扩展名）
        basename = Path(filename).stem

        # 黑名单词
        blacklist = {
            '简历', 'resume', 'cv', '附件', '文档', '同学', '先生', '女士',
            '求职者', '候选人',
        }

        # ========== 模式1: 去除时间戳前缀 ==========
        # "20250130_123456_职位-姓名（备注）" -> "职位-姓名（备注）"
        # 匹配开头的时间戳模式：数字_数字_
        basename = re.sub(r'^\d{8}_\d{6}_', '', basename)

        # ========== 模式2: "职位-姓名（备注）"（最常见）==========
        # 例如："财务信息化顾问-李景昱（中）"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})(?:（[^）]*）)?$', basename)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式3: "职位-姓名"（无括号）==========
        # 例如："产品经理-张三"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})$', basename)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式4: "姓名-简历" 或 "姓名-resume" ==========
        # 例如："李四-简历"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})-(?:简历|resume|cv|附件)$', basename, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式5: 纯姓名（只有2-4个汉字）==========
        # 例如："王五.pdf"
        if re.match(r'^[\u4e00-\u9fa5]{2,4}$', basename):
            name = basename.strip()
            if self._is_valid_name(name, blacklist):
                return name

        return None

    def _extract_education(self, text: str) -> List[Dict]:
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

        # 教育背景关键词
        keywords = ['教育', '学历', '教育背景', '学习经历', '教育经历', '学历背景']

        # 学历关键词（用于提取学历）- 按优先级排序
        degree_keywords = ['博士研究生', '博士', '硕士研究生', '硕士', '本科', '大专', '专科', '高中', '中专']

        # 学历正则模式（支持括号格式）
        degree_patterns = [
            r'\((博士研究生|博士|硕士研究生|硕士|本科|大专|专科|高中|中专)\)',  # (本科)
            r'（(博士研究生|博士|硕士研究生|硕士|本科|大专|专科|高中|中专)）',  # （本科）
            r'\s(博士研究生|博士|硕士研究生|硕士|本科|大专|专科|高中|中专)\s',  # 空格包围
            r'/(博士研究生|博士|硕士研究生|硕士|本科|大专|专科|高中|中专)',  # /本科
            r'\|(博士研究生|博士|硕士研究生|硕士|本科|大专|专科|高中|中专)',  # |本科
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

        if start_idx is None:
            return education_list

        # 解析教育经历
        i = start_idx
        while i < min(start_idx + 100, len(lines)):  # 扩大搜索范围到100行
            line = lines[i].strip()

            # 跳过空行和标题行
            if not line or any(keyword in line for keyword in keywords):
                i += 1
                continue

            # 遇到新段落，停止
            if any(keyword in line for keyword in ['工作经历', '项目经验', '技能', '联系方式', '实习经历', '专业技能']):
                break

            education = None

            # ========== 模式1: 学校名独立成行（包含"大学"或"学院"）==========
            if '大学' in line or '学院' in line:
                education = {
                    'school': line,
                    'degree': '',
                    'major': '',
                    'duration': ''
                }

                # 向后查找学历和专业（范围：后10行）
                for j in range(i + 1, min(i + 11, len(lines))):
                    next_line = lines[j].strip()

                    # 空行或新段落，停止
                    if not next_line:
                        break
                    if '大学' in next_line or '学院' in next_line:
                        break  # 遇到新学校，停止

                    # 提取学历（优先查找包含"/"的行，如"会计 / 硕士"）
                    if not education['degree']:
                        # 优先检查 "专业 / 学历" 格式
                        if '/' in next_line:
                            for degree in degree_keywords:
                                if degree in next_line:
                                    education['degree'] = degree
                                    # 同时提取专业（/前的部分）
                                    parts = next_line.split('/')
                                    if len(parts) > 0:
                                        education['major'] = parts[0].strip()
                                    break
                        # 检查括号格式，如 "软件工程(本科)" 或 "计算机科学与技术（硕士）"
                        else:
                            # 使用正则提取括号中的学历
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
                        time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', next_line)
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

            # ========== 模式2: 同一行包含学校+学历（如"上海大学 本科"）==========
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

            # 添加到列表
            if education and education['school']:
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
                            time_match = re.search(r'(\d{4})\s*[-.年]\s*\d{1,2}\s*[-.年—至到]\s*(\d{4}|\d{1,2}|至今)', next_line)
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

        return education_list

    def _extract_work_experience(self, text: str) -> List[Dict]:
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
        ]

        # 公司名识别模式
        company_patterns = [
            r'.*公司.*',  # 包含"公司"
            r'.*科技.*',  # 包含"科技"
            r'.*有限.*',  # 包含"有限"
            r'.*集团.*',  # 包含"集团"
            r'.*银行.*',  # 包含"银行"
            r'.*医院.*',  # 包含"医院"
            r'.*学校.*',  # 包含"学校"
        ]

        # 职位关键词
        position_keywords = ['工程师', '专员', '经理', '总监', '主管', '助理', '顾问',
                           '开发', '设计', '测试', '运营', '销售', '财务', '人事', '行政',
                           '分析师', '架构师', '产品经理', '执行', 'PM']

        # 查找工作经历段落（用于确定搜索范围）
        keywords = ['工作经历', '工作经验', '职业经历', '工作']
        lines = text.split('\n')
        start_idx = None
        end_idx = len(lines)

        for i, line in enumerate(lines):
            if any(keyword in line for keyword in keywords):
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

        # 第二步：对每个时间行，向前查找公司名和职位
        processed_indices = set()  # 记录已处理的行索引
        for time_idx in sorted(time_lines.keys()):
            if time_idx in processed_indices:
                continue

            duration = time_lines[time_idx]

            # 向前查找公司名和职位（范围：前5行）
            company = ''
            position = ''
            search_back_start = max(search_start, time_idx - 5)

            for j in range(time_idx - 1, search_back_start - 1, -1):
                if j in processed_indices:
                    break  # 遇到已处理的工作经历，停止

                line = lines[j].strip()
                if not line:
                    continue

                # 跳过明显不是公司名的行
                skip_patterns = ['项目职责', '项目业绩', '主要职责', '工作内容', '业绩',
                               '求职意向', '期望薪资', '期望城市']
                if any(skip in line for skip in skip_patterns):
                    continue

                # 检查是否是公司名（放宽条件）
                if not company:
                    # 优先匹配包含明确公司关键词的
                    if any(re.search(p, line) for p in company_patterns):
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

            # 如果没找到公司名，尝试从时间行本身提取
            time_line = lines[time_idx].strip()
            if not company:
                # 去掉时间部分，看是否有公司名
                company_part = time_line
                for pattern in time_patterns:
                    company_part = re.sub(pattern, '', company_part).strip()
                if company_part and any(re.search(p, company_part) for p in company_patterns):
                    company = company_part

            # 创建工作记录（只要有时间和职位/公司名之一就创建）
            if company or position:
                work_entry = {
                    'company': company if company else '',
                    'position': position,
                    'duration': duration,
                    'years': 0,
                    'responsibilities': ''
                }
                work_entry['years'] = self._extract_years_from_duration(duration)
                work_list.append(work_entry)
                processed_indices.add(time_idx)

                # 最多取5条
                if len(work_list) >= 5:
                    break

        return work_list

    def _calculate_work_years(self, work_experience: List[Dict]) -> int:
        """计算工作年限 - 改进版（累加所有工作经历）"""
        total_years = 0

        for work in work_experience:
            # 使用新方法提取年限
            years = self._extract_years_from_duration(work.get('duration', ''))
            total_years += years

        return int(total_years)

    def _extract_years_from_duration(self, duration: str) -> int:
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

        from datetime import datetime
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

    def _extract_project_experience(self, text: str) -> List[Dict]:
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

    def _extract_skills(self, text: str) -> List[str]:
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

    def _extract_skills_with_proficiency(self, text: str) -> Dict[str, List[str]]:
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
                    extracted = self._extract_skill_names(skill_text)
                    for skill in extracted:
                        # 标准化技能名称
                        standardized = SKILL_SYNONYMS.get(skill.lower(), skill)
                        skills_by_level[level].append(standardized)
                        skills_with_proficiency.add(standardized)

        # 提取所有技能（用于无熟练度标记的）
        all_skills = self._extract_skills(text)
        for skill in all_skills:
            standardized = SKILL_SYNONYMS.get(skill.lower(), skill)
            if standardized not in skills_with_proficiency:
                skills_by_level['mentioned'].append(standardized)

        # 去重
        for level in skills_by_level:
            skills_by_level[level] = list(set(skills_by_level[level]))

        return skills_by_level

    def _extract_skill_names(self, text: str) -> List[str]:
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
