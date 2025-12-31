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
