"""文本清理工具类"""
import re
import unicodedata
import logging
import chardet

logger = logging.getLogger(__name__)


class TextCleaner:
    """文本清理工具"""

    @staticmethod
    def clean_text(text: str, encoding: str = 'utf-8') -> str:
        """清理和规范化文本

        Args:
            text: 原始文本
            encoding: 文本编码

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 1. Unicode规范化（NFKC - 兼容性分解后规范化）
        text = unicodedata.normalize('NFKC', text)

        # 2. 移除组合字符（如变音符号）
        text = ''.join(char for char in text if not unicodedata.combining(char))

        # 3. 移除控制字符（保留换行符\n、制表符\t、回车符\r）
        # 移除ASCII控制字符（0x00-0x1F）中除了\n\t\r的字符
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

        # 4. 规范化空白字符
        # 替换各种空白字符为普通空格
        text = re.sub(r'[\u00A0\u2000-\u200B\u2028-\u202F\u205F\u3000]', ' ', text)
        # 多个连续换行最多保留2个
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 多个空格/制表符合并为一个
        text = re.sub(r'[ \t]+', ' ', text)
        # 多个连续的空行合并为一个
        text = re.sub(r'\n \n', '\n\n', text)

        # 5. 去除首尾空白
        text = text.strip()

        # 6. 处理PDF解析导致的单字行问题（如"东\n北\n农\n业"合并为"东北农业"）
        # 检测连续的单字行并合并
        lines = text.split('\n')
        merged_lines = []
        i = 0

        # 定义不应该被合并的section headers（这些通常是独立的标题）
        section_headers = {
            '教育背景', '学习经历', '教育经历', '学历背景',
            '工作经历', '项目经验', '项目经历', '实习经历', '科研经历',
            '专业技能', '技能', '联系方式', '自我评价', '个人优势', '获奖情况',
            '求职意向', '应聘', '意向', '岗位', '职位', '专业背景'
        }

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                merged_lines.append(line)
                i += 1
                continue

            # 如果是section header，不合并，直接添加
            if line in section_headers:
                merged_lines.append(line)
                i += 1
                continue

            # 检查是否是短行（可能是被拆分的文本）
            # 短行定义：1-5个字符，且主要是中文/数字/标点
            is_short_line = (
                len(line) <= 5 and
                re.match(r'^[\u4e00-\u9fa5()（）\-/\d.年月]+$', line)
            )

            if is_short_line:
                # 向后查看是否还有类似的短行，连续合并
                merged_text = line
                j = i + 1
                # 最多合并20行
                while j < len(lines) and j < i + 20:
                    next_line = lines[j].strip()
                    # 空行停止
                    if not next_line:
                        break
                    # 如果下一行是section header，停止合并
                    if next_line in section_headers:
                        break
                    # 如果下一行也是短行
                    next_is_short = (
                        len(next_line) <= 5 and
                        re.match(r'^[\u4e00-\u9fa5()（）\-/\d.年月]+$', next_line)
                    )
                    if next_is_short:
                        merged_text += next_line
                        j += 1
                    else:
                        # 遇到长行，停止合并
                        break

                # 如果合并后的文本长度���理（超过6个字符），使用合并版本
                if len(merged_text) > 6:
                    merged_lines.append(merged_text)
                    i = j
                else:
                    merged_lines.append(line)
                    i += 1
            else:
                merged_lines.append(line)
                i += 1

        text = '\n'.join(merged_lines)

        # 7. 移除行首的section header（如"教育背景东北..."变为"东北..."）
        # 但保留header所在行，因为解析器需要这些来定位段落
        # 注释掉此功能，因为移除section header会导致解析器找不到段落
        # section_headers = ['教育背景', '学习经历', '教育经历', '学历背景', '工作经历', '项目经验', '实习经历',
        #                   '专业技能', '技能', '联系方式', '自我评价', '个人优势', '获奖情况']
        # lines = text.split('\n')
        # cleaned_lines = []
        # for line in lines:
        #     # 移除行首的section header
        #     for header in section_headers:
        #         if line.startswith(header):
        #             line = line[len(header):].strip()
        #             break
        #     cleaned_lines.append(line)
        # text = '\n'.join(cleaned_lines)

        return text

    @staticmethod
    def detect_encoding(text_bytes: bytes) -> str:
        """检测文本编码

        Args:
            text_bytes: 文本字节

        Returns:
            检测到的编码名称（默认utf-8）
        """
        try:
            result = chardet.detect(text_bytes)
            detected_encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)

            if confidence < 0.7:
                logger.warning(
                    f"编码检测置信度较低: {confidence:.2f}, "
                    f"检测编码: {detected_encoding}, 使用utf-8"
                )
                return 'utf-8'

            return detected_encoding
        except Exception as e:
            logger.error(f"编码检测失败: {e}, 使用utf-8")
            return 'utf-8'

    @staticmethod
    def clean_html_entities(text: str) -> str:
        """清理HTML实体字符

        Args:
            text: 包含HTML实体的文本

        Returns:
            清理后的文本
        """
        # 常见HTML实体映射
        html_entities = {
            '&nbsp;': ' ',
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&apos;': "'",
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™',
        }

        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)

        return text
