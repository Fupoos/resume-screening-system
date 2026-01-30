"""简历解析器主类 - 协调各提取器"""
import re
import jieba
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 导入各个提取器
from app.services.parsers.basic_info_extractor import BasicInfoExtractor
from app.services.parsers.education_extractor import EducationExtractor
from app.services.parsers.experience_extractor import ExperienceExtractor
from app.services.parsers.project_extractor import ProjectExtractor
from app.services.parsers.skills_extractor import SkillsExtractor


class ResumeParser:
    """简历解析器 - 重构版

    将原有的单文件拆分为多个模块：
    - BasicInfoExtractor: 姓名、电话、邮箱
    - EducationExtractor: 学历信息
    - ExperienceExtractor: 工作经历
    - ProjectExtractor: 项目经历
    - SkillsExtractor: 技能提取
    """

    def __init__(self):
        """初始化简历解析器"""
        # 设置jieba分词
        jieba.setLogLevel(jieba.logging.INFO)

    def parse_resume(self, file_path: str, email_subject: Optional[str] = None) -> Dict:
        """解析简历文件

        Args:
            file_path: 简历文件路径
            email_subject: 邮件标题（可选）

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
        """解析PDF简历 - 混合策略获取完整文本

        策略优先级：
        1. pymupdf4llm (主要) - 布局感知，处理复杂布局、表格、分栏等
        2. 原生PyMuPDF (补充) - 提取联系信息（页头页尾）和education_history
        3. pdfplumber (最后备选) - 兼容性方案

        说明：pymupdf4llm会跳过页头页尾，需要用原生PyMuPDF补充联系信息
        """
        from app.utils.text_cleaner import TextCleaner

        # 策略1: pymupdf4llm (主要) - 布局感知解析
        try:
            import pymupdf4llm

            logger.info(f"使用pymupdf4llm解析PDF: {file_path}")

            # 转换为Markdown（保留格式，有助于理解文档结构）
            md_text = pymupdf4llm.to_markdown(file_path)

            # 清理文本
            text = TextCleaner.clean_text(md_text)
            logger.info(f"pymupdf4llm解析完成，文本长度: {len(text)} 字符")

            result = self._parse_text(text, email_subject=email_subject, filename=file_path)

            # 策略1.5: 使用原生PyMuPDF补充联系信息（pymupdf4llm会跳过页头页尾）
            try:
                import fitz  # PyMuPDF
                # 只提取联系信息（phone, email）
                contact_text = ""
                with fitz.open(file_path) as doc:
                    for page in doc:
                        contact_text += page.get_text("text") + "\n"

                # 清理联系信息文本
                contact_text = TextCleaner.clean_text(contact_text)

                # 如果pymupdf4llm没提取到电话，尝试从contact_text提取
                if not result.get('phone'):
                    from app.services.parsers.basic_info_extractor import BasicInfoExtractor
                    phone = BasicInfoExtractor.extract_phone(contact_text)
                    if phone:
                        result['phone'] = phone
                        logger.info(f"从原生PyMuPDF补充提取电话: {phone}")

                # 如果pymupdf4llm没提取到邮箱，尝试从contact_text提取
                if not result.get('email'):
                    from app.services.parsers.basic_info_extractor import BasicInfoExtractor
                    email = BasicInfoExtractor.extract_email(contact_text)
                    if email:
                        result['email'] = email
                        logger.info(f"从原生PyMuPDF补充提取邮箱: {email}")

            except Exception as e:
                logger.warning(f"原生PyMuPDF补充联系信息失败: {e}")

            # 策略1.6: 始终用原生PyMuPDF提取教育背景（pymupdf4llm会跳过页头的教育部分）
            try:
                import fitz  # PyMuPDF
                edu_text = ""
                with fitz.open(file_path) as doc:
                    for page in doc:
                        edu_text += page.get_text("text") + "\n"

                # 清理文本
                edu_text = TextCleaner.clean_text(edu_text)

                # 提取education_history
                from app.services.parsers.education_extractor import EducationExtractor
                edu_history = EducationExtractor.extract_education(edu_text)
                if edu_history:
                    result['education_history'] = edu_history
                    logger.info(f"从原生PyMuPDF提取到{len(edu_history)}条教育经历")

                    # 重新计算education和education_level
                    degree_mapping = {
                        '博士研究生': '博士', '博士': '博士',
                        '硕士研究生': '硕士', '硕士': '硕士',
                        '学士': '本科', '本科': '本科',
                        '大专': '大专', '专科': '大专',
                        '高中': '高中', '中专': '高中',
                    }
                    education_order = ['博士', '硕士', '本科', '大专', '高中']
                    for edu in education_order:
                        for edu_item in edu_history:
                            degree = edu_item.get('degree', '')
                            school_name = edu_item.get('school', '')
                            normalized_degree = degree_mapping.get(degree, degree)
                            if normalized_degree == edu:
                                # 优先选择有有效学校名称的记录
                                if school_name and school_name != '未知':
                                    result['education'] = edu
                                    # 计算education_level
                                    if any(edu_level in degree for edu_level in ['大专', '专科', '中专', '高中', '高职']):
                                        result['education_level'] = degree_mapping.get(degree.split('(')[0], degree)
                                    else:
                                        from app.data.university_database import classify_university
                                        result['education_level'] = classify_university(school_name) if school_name else '双非'
                                    logger.info(f"学历：{result['education']}，学校：{school_name}，等级：{result['education_level']}")
                                    break
                                # 如果还没有找到任何记录，先设置这个（即使学校名为空）
                                elif not result.get('education'):
                                    result['education'] = edu
                        # 只有找到有有效学校名的记录才停止
                        if result.get('education') and result.get('education_level'):
                            # 检查当前使用的记录是否有有效学校名
                            current_has_valid_school = False
                            for edu_item in edu_history:
                                if edu_item.get('degree', '') == result.get('education', ''):
                                    if edu_item.get('school', '') and edu_item.get('school', '') != '未知':
                                        current_has_valid_school = True
                                        break
                            if current_has_valid_school:
                                break

            except Exception as e:
                logger.warning(f"原生PyMuPDF提取教育经历失败: {e}")

            return result

        except ImportError:
            logger.warning("pymupdf4llm未安装，使用原生PyMuPDF作为fallback")
        except Exception as e:
            logger.warning(f"pymupdf4llm解析失败: {e}，尝试fallback方案")

        # 策略2: 原生PyMuPDF (fallback)
        try:
            import fitz  # PyMuPDF
            logger.info(f"使用原生PyMuPDF解析PDF: {file_path}")

            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    # 提取文本（使用"text"模式，适合文本型PDF）
                    page_text = page.get_text("text")
                    text += page_text + "\n"

            # 清理文本
            text = TextCleaner.clean_text(text)
            logger.info(f"原生PyMuPDF解析完成，文本长度: {len(text)} 字符")

            return self._parse_text(text, email_subject=email_subject, filename=file_path)

        except ImportError:
            logger.warning("PyMuPDF未安装，尝试pdfplumber作为最后备选")

        # 策略3: pdfplumber (最后备选)
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
            logger.error("PDF解析库未安装（pymupdf4llm、PyMuPDF和pdfplumber都不可用）")
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
            'education_level': None,
            'work_years': None,
            'skills': [],
            'work_experience': [],
            'project_experience': [],
            'education_history': [],
            'raw_text': text
        }

        # 提取基本信息
        result['phone'] = BasicInfoExtractor.extract_phone(text)
        result['email'] = BasicInfoExtractor.extract_email(text)

        # 优先级1: 从邮件标题提取姓名
        if email_subject:
            result['candidate_name'] = BasicInfoExtractor.extract_name_from_email_subject(email_subject)
            if result['candidate_name']:
                logger.info(f"从邮件主题提取姓名: {result['candidate_name']}")

        # 优先级2: 从文件名提取姓名
        if not result['candidate_name'] and filename:
            result['candidate_name'] = BasicInfoExtractor.extract_name_from_filename(filename)
            if result['candidate_name']:
                logger.info(f"从文件名提取姓名: {result['candidate_name']}")

        # 优先级3: 从简历正文提取姓名
        if not result['candidate_name']:
            result['candidate_name'] = BasicInfoExtractor.extract_name(text)
            if result['candidate_name']:
                logger.info(f"从简历正文提取姓名: {result['candidate_name']}")

        # 提取教育背景
        result['education_history'] = EducationExtractor.extract_education(text)
        if result['education_history']:
            # 标准化学历映射（学士→本科等，包含英文）
            degree_mapping = {
                '博士研究生': '博士', '博士': '博士',
                '硕士研究生': '硕士', '硕士': '硕士',
                '学士': '本科', '本科': '本科',
                '大专': '大专', '专科': '大专',
                '高中': '高中', '中专': '高中',
                # 英文学历映射
                'Ph.D': '博士', 'PhD': '博士', 'Doctor': '博士', 'Doctorate': '博士',
                'Master': '硕士', 'Masters': '硕士', 'M.B.A': '硕士', 'MBA': '硕士',
                'Bachelor': '本科', 'Bachelors': '本科', 'B.S': '本科', 'B.A': '本科', 'B.Sc': '本科', 'BBA': '本科',
                'Associate': '大专', 'College': '大专'
            }

            # 取最高学历（优先选择有有效学校名称的记录）
            education_order = ['博士', '硕士', '本科', '大专', '高中']
            highest_edu_record = None
            for edu in education_order:
                for edu_history in result['education_history']:
                    degree = edu_history.get('degree', '')
                    school = edu_history.get('school', '')
                    # 标准化学历名称
                    normalized_degree = degree_mapping.get(degree, degree)
                    if normalized_degree == edu:
                        # 只选择有有效学校名称的记录（school不为空且不是"未知"）
                        if school and school != '未知':
                            result['education'] = edu
                            highest_edu_record = edu_history
                            break
                        # 如果还没有找到任何记录，先保存这个（可能学校为空的记录）
                        if highest_edu_record is None:
                            result['education'] = edu
                            highest_edu_record = edu_history
                if result['education'] and highest_edu_record.get('school') not in ['', '未知']:
                    # 只有找到有有效学校名的记录才停止
                    break

            # 如果还没找到，直接检查原始学历
            if not result['education']:
                for edu_history in result['education_history']:
                    degree = edu_history.get('degree', '')
                    if degree:
                        result['education'] = degree_mapping.get(degree, degree)
                        highest_edu_record = edu_history
                        break

            # 使用本地学校分类（仅对本科及以上学历）
            if highest_edu_record:
                degree = highest_edu_record.get('degree', '')
                school_name = highest_edu_record.get('school', '')

                # 大专/专科/中专/高中学历不使用211/985/双非分类
                if any(edu in degree for edu in ['大专', '专科', '中专', '高中', '高职']):
                    degree_level_mapping = {'大专': '专科', '专科': '专科', '中专': '中专', '高中': '高中', '高职': '高职'}
                    result['education_level'] = degree_level_mapping.get(degree.split('(')[0], '专科')
                else:
                    from app.data.university_database import classify_university
                    if not school_name:
                        result['education_level'] = '双非'
                    else:
                        result['education_level'] = classify_university(school_name)
                logger.info(f"学历：{result['education']}，学校：{school_name}，等级：{result['education_level']}")

        # 备用方案：从基本信息部分提取学历（处理"学 历:本科(211)"格式）
        if not result['education'] or not result['education_level']:
            lines = text.split('\n')
            basic_info_section = False
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # 检测基本信息段落
                if '基本信息' in line_stripped:
                    basic_info_section = True
                    continue
                # 如果离开基本信息段落，停止
                if basic_info_section and any(kw in line_stripped for kw in ['工作经历', '项目经验', '教育经历', '技能']):
                    break
                # 在基本信息段落内查找学历
                if basic_info_section and ('学 历:' in line_stripped or '学历:' in line_stripped):
                    # 提取学历（支持"本科(211)"格式）
                    degree_match = re.search(r'[:：]\s*([本科大专高中中专博士硕士学士]+)(?:\(([211985双非QS前\d]+)\))?', line_stripped)
                    if degree_match:
                        degree = degree_match.group(1)
                        # 标准化学历名称
                        degree_mapping = {'学士': '本科', '硕士研究生': '硕士', '博士研究生': '博士'}
                        degree = degree_mapping.get(degree, degree)
                        result['education'] = degree
                        # 如果有等级标签（如211），提取它
                        if degree_match.group(2):
                            level_tag = degree_match.group(2)
                            result['education_level'] = level_tag
                        logger.info(f"从基本信息提取学历：{result['education']}")
                    break

        # 优先级1: 从邮件主题提取工作年限（第一优先级）
        if email_subject and result['work_years'] is None:
            work_years_from_subject = BasicInfoExtractor.extract_work_years_from_subject(email_subject)
            if work_years_from_subject is not None:
                result['work_years'] = work_years_from_subject
                logger.info(f"从邮件主题提取工作年限: {result['work_years']}年")

        # 提取工作经历
        result['work_experience'] = ExperienceExtractor.extract_work_experience(text)

        # 优先级2: 只有当邮件主题没有提取到工作年限时，才从工作经历计算
        if result['work_years'] is None and result['work_experience']:
            result['work_years'] = ExperienceExtractor.calculate_work_years(result['work_experience'])

        # 提取项目经历
        result['project_experience'] = ProjectExtractor.extract_project_experience(text)

        # 提取技能关键词
        result['skills'] = SkillsExtractor.extract_skills(text)

        # 如果工作年限仍未确定，设为0
        if result['work_years'] is None:
            result['work_years'] = 0

        return result
