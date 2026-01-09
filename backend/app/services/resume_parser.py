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

            # 使用本地学校分类
            if highest_edu_record and highest_edu_record.get('school'):
                from app.data.university_database import classify_university
                school_name = highest_edu_record.get('school', '')
                result['education_level'] = classify_university(school_name)
                logger.info(f"学历：{result['education']}，学校：{school_name}，等级：{result['education_level']}")

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
        3. 139-1234-5678（带横杠）
        4. （+86）139-1234-5678（带国家代码）
        5. Tel:(+86)139-1234-5678（英文格式）
        """
        # 预处理：移除所有空格和中文空格
        text_no_spaces = text.replace(' ', '').replace('　', '')

        # 先尝试直接匹配11位手机号
        match = re.search(r'1[3-9]\d{9}', text_no_spaces)
        if match:
            return match.group()

        # 尝试匹配带国家代码的格式：(+86) 139-1234-5678 或 （+86）139-1234-5678
        match = re.search(r'[\(（]\+86[\)）]\s*-?\s*1[3-9]\d{9}', text_no_spaces)
        if match:
            # 提取纯手机号
            phone_match = re.search(r'1[3-9]\d{9}', match.group())
            if phone_match:
                return phone_match.group()

        # 尝试匹配带横杠的手机号
        match = re.search(r'1[3-9]\d[-\s]?\d{4}[-\s]?\d{4}', text_no_spaces)
        if match:
            # 清理横杠和空格
            phone = match.group()
            phone = phone.replace('-', '').replace(' ', '')
            if len(phone) == 11:
                return phone

        # 匹配座机号（从原文）
        match = re.search(r'\d{3,4}-\d{7,8}', text)
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
            '求职信息', '出生年月', '政治面貌', '工作年限',
            '个人信息', '个人总结', '个人简介', '个人评价', '优势亮点',
            '掌握技能', '资格证书',
            '性别', '手机', '电话', '邮箱', '出生日期', '出生年月', '年龄',
            '籍贯', '地址', '婚姻状况', '民族', '现居住地', '通讯地址',
            '邮政编码', '最高学历', '期望薪资', '期望城市', '应聘岗位',
            '求职信息', '工作年限', '政治面貌',
            #第二轮：补充无效名字
            '同学', '微信号', '手机号', '先生', '女士', '小姐',
            #第三轮：更多字段标签
            '出生年日', '工作时长', '联系电话', '现所在地', '相关课程',
            '项目描述', '发件人', '实习留用', '综合绩点', '手机号码',
            '学校住址', '工作地点', '居住地址', '户籍地址', '电子邮箱',
            '主修专业', '所学专业', '专业名称',
            '应用化学', '计算机', '财务管理', '市场营销', '工商管理',
            '信息管理', '软件技术', '网络工程', '电子信息', '机械设计',
            '土木工程', '材料科学', '生物工程', '环境工程', '化学工程',
            #第四轮：更多无效提取结果
            '意向城市', '户籍', '现居城市', '毕业院校', '英语水平',
            '英语', '产品运营', '费用报销', '发送时间', '发送日期', '后端开发',
            '前端开发', '测试开发', '运营管理', '项目管理', '系统架构',
            '数据分析', '数据管理', '技术支持', '软件开发', '系统设计',
            #第五轮：更多字段标签
            '收件人', '客户成功', '求职类型', '业务支持', '客户服务',
            '售后服务', '销售支持', '市场支持', '运营支持', '技术总监',
            '产品总监', '运营总监', '销售经理', '市场经理', '项目经理',
            # 信息字段（原有）
            '男', '女', '年龄', '电话', '邮箱', '邮箱', '地址', '籍贯',
            '学历', '学位', '专业', '学校', '毕业', '院校',
            # 学历
            '本科', '硕士', '博士', '大专', '专科', '高中', '中专',
            '专升本', '研究生', '本科生', '硕士生', '博士生',
            '本科学位', '硕士学位', '博士学位', '双一流',
            # 学科/专业
            '会计', '会计学', '审计', '统计学', '软件工程', '电子信息',
            '计算机科学', '通信工程', '机械工程', '数据科学',
            '人工智能', '自动化', '电气工程', '财务管理',
            # 职位/岗位相关
            '总账会计', '财务专员', '销售总监', '软件工程师', '产品经理',
            '项目经历', '实习经历', '工作内容', '主要职责',
            # 城市/地点
            '上海', '北京', '深圳', '广州', '杭州', '成都', '武汉',
            '西安', '南京', '重庆', '天津', '苏州', '长沙', '青岛', '长春',
            # 公司名（常见误识别）
            '明源云', '用友', '金蝶', '卫泰集团',
            # 其他常见非姓名词汇
            '个人介绍', '基本信息', '专业技能', '主修课程', '获奖情况',
            '证书情况', '语言能力', '计算机能力', '工作内容',
        }

        #模式：支持带空格的姓名（如"李 晓 斌"）
        for line in lines[:20]:
            line = line.strip()
            if not line:
                continue

            # 匹配 "李 晓 斌" 或 "李 晓" 格式（姓和名之间有空格）
            # 支持二到三个字之间有空格
            match = re.search(r'^([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])(?:\s+([\u4e00-\u9fa5]))?', line)
            if match:
                # 提取姓名（去除空格）
                parts = [g for g in match.groups() if g]
                name = ''.join(parts)
                # 验证：2-4个字，且在黑名单之外
                if 2 <= len(name) <= 4 and self._is_valid_name(name, blacklist):
                    logger.info(f"从带空格格式提取姓名: {line} → {name}")
                    return name

        # 模式0: 查找行首的姓名（常见格式：姓名 求职意向:xxx）
        for line in lines[:20]:
            line = line.strip()
            # 跳过空行和太长的行
            if not line or len(line) > 50:
                continue
            # 匹配行首的2-4个汉字（后面可能跟空格、"求职意向"、"应聘"等）
            # 例如："刘泽钰 求职意向:项目经理" 或 "张三 应聘Java开发"
            match = re.search(r'^([一-龥]{2,4})\s+(求职意向|应聘|意向|岗位)', line)
            if match:
                name = match.group(1).strip()
                if self._is_valid_name(name, blacklist):
                    return name
            
            # 匹配行首的2-4个汉字加冒号（可能是姓名但后面是其他信息）
            # 例如："刘泽钰: 男" 或 "张三：1990年"
            match = re.search(r'^([一-龥]{2,4})\s*[:：]', line)
            if match:
                name = match.group(1).strip()
                if self._is_valid_name(name, blacklist):
                    return name

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

        # 模式4: 在联系方式附近查找姓名（邮箱/电话前后）
        common_surname_chars = set('赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉��薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董粱杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍万柯卢莫房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉钮龚')
        for i, line in enumerate(lines):
            line = line.strip()
            # 查找包含邮箱或电话号码的行
            if '@' in line or re.search(r'1[3-9]\d{9}', line):
                # 检查前1-3行是否有独立成行的2-4个汉字
                for j in range(max(0, i-3), i):
                    check_line = lines[j].strip()
                    # 匹配独立的2-4个汉字（可能前后有空格）
                    match = re.search(r'^[\s]*([\u4e00-\u9fa5]{2,4})[\s]*$', check_line)
                    if match:
                        name = match.group(1).strip()
                        # 严格检查：不能是黑名单词，第一个字必须是常见姓氏
                        if name not in blacklist and name[0] in common_surname_chars:
                            if self._is_valid_name(name, blacklist):
                                return name

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

        # ========== 模式2: "【职位_地点_薪资】姓名_年限"（BOSS直聘格式）==========
        # 例如："【财务咨询顾问（深圳）_深圳_10-15K】邹喆_2年.pdf"
        match = re.search(r'】([\u4e00-\u9fa5]{2,4})_', basename)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 职位-姓名-其他（支持复杂分隔符）==========
        # 例如："张先寿-销售管理&IT项目管理 案例-简历25-12.pdf"
        # 例如："市场运营助理-Yoana Li 李珮瑶（中）.pdf"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})[-—]', basename)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                logger.info(f"从文件名提取姓名（职位-姓名格式）: {basename} → {name}")
                return name

        # ========== 姓名（备注）格式 ==========
        # 例如："李珮瑶（中）" 或 "李珮瑶(中)"
        # 例如："张三（男）" 或 "张三(男)"
        match = re.search(r'^([\u4e00-\u9fa5]{2,4})[（\(][^）\)]*[）\)]', basename)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                logger.info(f"从文件名提取姓名（姓名备注格式）: {basename} → {name}")
                return name

        # ========== 模式3: "职位-姓名（备注）"（最常见）==========
        # 例如："财务信息化顾问-李景昱（中）"
        match = re.search(r'-([\u4e00-\u9fa5]{2,4})(?:（[^）]*）)?$', basename)
        if match:
            name = match.group(1).strip()
            if self._is_valid_name(name, blacklist):
                return name

        # ========== 模式4: "职位-姓名"（无括号）==========
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

        # 教育背景关键词（用于定位教育背景段落，不包含"学历"因为"学历"可能出现在数据行中）
        keywords = ['教育背景', '学习经历', '教育经历', '学历背景', '专业背景']

        # 学历关键词（用于提取学历）- 按优先级排序
        degree_keywords = ["博士研究生", "博士", "硕士研究生", "硕士", "学士", "本科", "大专", "专科", "高中", "中专"]

        # 学历正则模式（支持括号格式，包括带前缀的如"(工学硕士)"）
        degree_patterns = [
            r'\((?:[^\)]*?)?(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)\)',  # (本科)或(工学硕士)
            r'（(?:[^）]*?)?(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)）',  # （本科）或（工学硕士）
            r'\s(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)\s',  # 空格包围
            r'/(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)',  # /本科
            r'\|(博士研究生|博士|硕士研究生|硕士|学士|本科|大专|专科|高中|中专)',  # |本科
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
            # 后处理：从school字段中提取degree并清理school名称
            education_list = self._post_process_education(education_list)
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

                    # ========== 优先级1: 检查"专业(学历)"括号格式（如"华东理工大学 专业催化(工学硕士)"）==========
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

            # ========== 模式2: 同一行包��"学校 / 学历"格式 ==========
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

        # 后处理：从school��段中提取degree并清理school名称
        education_list = self._post_process_education(education_list)
        return education_list

    def _post_process_education(self, education_list: List[Dict]) -> List[Dict]:
        """后处理教育经历列表，从school字段中提取degree并清理school名称"""
        degree_keywords = ['博士', '硕士', '本科', '大专', '高中', '专升本', '中专', 'MBA', 'EMBA']

        for education in education_list:
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
                                      '英语等级', 'CET', '雅思', '托福', 'GRE', '学历 ']
                if any(kw in school for kw in non_school_keywords):
                    # 如果包含这些关键词，清空school（这不是有效的学校信息）
                    education['school'] = ''
                # 检查school是否以"学历"开头（无效）
                if school.startswith('学历') or school.startswith('学历:'):
                    education['school'] = ''

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

                work_desc_prefixes = ['负责', '协助', '主导', '参与', '完成', '执行',
                                     '开展', '跟进', '管理', '策划', '设计', '开发']
                if any(line.startswith(prefix) for prefix in work_desc_prefixes):
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

            # 如果没找到公司名，尝试从时间行本身提取
            time_line = lines[time_idx].strip()
            if not company:
                # 去掉时间部分，看是否有公司名
                company_part = time_line
                for pattern in time_patterns:
                    company_part = re.sub(pattern, '', company_part).strip()
                if company_part and any(re.search(p, company_part) for p in company_patterns):
                    company = company_part

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
