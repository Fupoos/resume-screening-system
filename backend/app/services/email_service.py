"""邮箱服务 - 处理IMAP连接和邮件获取"""
import imaplib
from email import message
from email import message_from_bytes
from email.header import decode_header
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """邮箱服务类"""

    def __init__(
        self,
        email_address: str,
        auth_code: str,
        imap_server: str = "imap.exmail.qq.com",
        imap_port: int = 993,
        folder: str = "INBOX"
    ):
        """初始化邮箱服务

        Args:
            email_address: 邮箱地址
            auth_code: 授权码
            imap_server: IMAP服务器地址
            imap_port: IMAP端口
            folder: 监听文件夹
        """
        self.email_address = email_address
        self.auth_code = auth_code
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.folder = folder
        self.client = None

    def connect(self) -> bool:
        """连接到IMAP服务器

        Returns:
            连接是否成功
        """
        try:
            # 创建SSL连接
            self.client = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)

            # 登录
            self.client.login(self.email_address, self.auth_code)

            # 选择文件夹
            self.client.select(self.folder)

            logger.info(f"成功连接到邮箱: {self.email_address}")
            return True

        except Exception as e:
            logger.error(f"连接邮箱失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.client:
            try:
                self.client.close()
                self.client.logout()
                logger.info("已断开邮箱连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {e}")

    def fetch_unread_emails(
        self,
        filter_keywords: Optional[List[str]] = None,
        sender_whitelist: Optional[List[str]] = None
    ) -> List[Dict]:
        """获取未读邮件

        Args:
            filter_keywords: 过滤关键词列表（邮件主题包含这些关键词）
            sender_whitelist: 发件人白名单

        Returns:
            邮件列表
        """
        if not self.client:
            if not self.connect():
                return []

        emails = []

        # 统计附件信息
        attachment_count = 0
        attachment_types = {}

        try:
            # 搜索未读邮件
            status, messages = self.client.search(None, 'UNSEEN')

            if status != 'OK':
                logger.warning("搜索邮件失败")
                return []

            # 获取邮件ID列表
            email_ids = messages[0].split()

            logger.info(f"找到 {len(email_ids)} 封未读邮件")

            for idx, email_id in enumerate(email_ids):
                try:
                    if idx % 50 == 0:
                        logger.info(f"正在处理第 {idx+1}/{len(email_ids)} 封邮件...")

                    # 获取邮件
                    status, msg_data = self.client.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # 解析邮件
                    raw_email = msg_data[0][1]
                    msg = message_from_bytes(raw_email)

                    # 提取邮件信息
                    email_info = self._parse_email(msg, email_id.decode())

                    # 统计附件
                    if email_info['attachments']:
                        attachment_count += len(email_info['attachments'])
                        for att in email_info['attachments']:
                            ext = att['filename'].split('.')[-1].lower()
                            attachment_types[ext] = attachment_types.get(ext, 0) + 1

                    # 过滤邮件
                    if self._should_filter_email(email_info, filter_keywords, sender_whitelist):
                        # 记录被过滤的邮件（前5封）
                        if len(emails) < 5 and email_info['attachments']:
                            logger.info(f"邮件被过滤: 主题='{email_info['subject'][:50]}', 附件={[a['filename'] for a in email_info['attachments']]}")
                        continue

                    emails.append(email_info)

                except Exception as e:
                    logger.error(f"解析邮件 {email_id} 失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"获取邮件失败: {e}")

        # 输出统计信息
        logger.info(f"附件统计: 总计{attachment_count}个附件, 类型分布: {dict(attachment_types)}")

        return emails

    def fetch_read_emails(
        self,
        limit: int = 500,
        filter_keywords: Optional[List[str]] = None,
        sender_whitelist: Optional[List[str]] = None
    ) -> List[Dict]:
        """获取已读邮件（最新的N封）

        Args:
            limit: 获取邮件数量限制
            filter_keywords: 过滤关键词列表（邮件主题包含这些关键词）
            sender_whitelist: 发件人白名单

        Returns:
            邮件列表
        """
        if not self.client:
            if not self.connect():
                return []

        emails = []

        try:
            # 搜索所有邮件（包括已读）
            status, messages = self.client.search(None, 'SEEN')

            if status != 'OK':
                logger.warning("搜索邮件失败")
                return []

            # 获取邮件ID列表
            email_ids = messages[0].split()

            # 只取最新的limit封邮件
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids

            logger.info(f"找到 {len(email_ids)} 封已读邮件（限制: {limit}封）")

            # 统计附件信息
            attachment_count = 0
            attachment_types = {}

            for idx, email_id in enumerate(email_ids):
                try:
                    if idx % 50 == 0:
                        logger.info(f"正在处理第 {idx+1}/{len(email_ids)} 封已读邮件...")

                    # 获取邮件
                    status, msg_data = self.client.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # 解析邮件
                    raw_email = msg_data[0][1]
                    msg = message_from_bytes(raw_email)

                    # 提取邮件信息
                    email_info = self._parse_email(msg, email_id.decode())

                    # 统计附件
                    if email_info['attachments']:
                        attachment_count += len(email_info['attachments'])
                        for att in email_info['attachments']:
                            ext = att['filename'].split('.')[-1].lower()
                            attachment_types[ext] = attachment_types.get(ext, 0) + 1

                    # 过滤邮件
                    if self._should_filter_email(email_info, filter_keywords, sender_whitelist):
                        # 记录被过滤的邮件（前5封）
                        if len(emails) < 5 and email_info['attachments']:
                            logger.info(f"邮件被过滤: 主题='{email_info['subject'][:50]}', 附件={[a['filename'] for a in email_info['attachments']]}")
                        continue

                    emails.append(email_info)

                except Exception as e:
                    logger.error(f"解析邮件 {email_id} 失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"获取邮件失败: {e}")

        # 输出统计信息
        logger.info(f"附件统计: 总计{attachment_count}个附件, 类型分布: {dict(attachment_types)}")

        return emails

    def fetch_recent_emails(
        self,
        limit: int = 20,
        filter_keywords: Optional[List[str]] = None,
        sender_whitelist: Optional[List[str]] = None
    ) -> List[Dict]:
        """获���最近的N封邮件（包括已读和未读，按时间从近到远）

        Args:
            limit: 获取邮件数量限制（默认20封）
            filter_keywords: 过滤关键词列表（邮件主题包含这些关键词）
            sender_whitelist: 发件人白名单

        Returns:
            邮件列表（按时间从近到远排序）
        """
        if not self.client:
            if not self.connect():
                return []

        emails = []

        try:
            # 搜索所有邮件（已读+未读）
            status, messages = self.client.search(None, 'ALL')

            if status != 'OK':
                logger.warning("搜索邮件失败")
                return []

            # 获取邮件ID列表
            email_ids = messages[0].split()

            # 只取最近的limit封邮件（从近到远）
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            # 反转列表，使其从最近的开始
            email_ids = list(reversed(email_ids))

            logger.info(f"找到 {len(email_ids)} 封最近的邮件（从近到远，限制: {limit}封）")

            # 统计附件信息
            attachment_count = 0
            attachment_types = {}

            for idx, email_id in enumerate(email_ids):
                try:
                    logger.info(f"正在处理第 {idx+1}/{len(email_ids)} 封邮件...")

                    # 获取邮件
                    status, msg_data = self.client.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        logger.warning(f"获取邮件 {email_id} 失败，状态码: {status}")
                        continue

                    # 解析邮件
                    raw_email = msg_data[0][1]
                    msg = message_from_bytes(raw_email)

                    # 提取邮件信息
                    email_info = self._parse_email(msg, email_id.decode())

                    # 记录邮件基本信息
                    logger.info(
                        f"邮件 {idx+1}: 主题='{email_info['subject'][:50]}', "
                        f"发件人='{email_info['sender'][:30]}', "
                        f"附件数={len(email_info['attachments'])}"
                    )

                    # 统计附件
                    if email_info['attachments']:
                        attachment_count += len(email_info['attachments'])
                        for att in email_info['attachments']:
                            ext = att['filename'].split('.')[-1].lower()
                            attachment_types[ext] = attachment_types.get(ext, 0) + 1

                    # 过滤邮件
                    should_filter = self._should_filter_email(email_info, filter_keywords, sender_whitelist)
                    if should_filter:
                        # 记录被过滤的邮件（前10封）
                        if idx < 10:
                            logger.info(
                                f"邮件被过滤: 主题='{email_info['subject'][:50]}', "
                                f"附件={[a['filename'] for a in email_info['attachments']]}, "
                                f"原因={self._get_filter_reason(email_info, filter_keywords, sender_whitelist)}"
                            )
                        continue

                    # 添加到结果列表
                    emails.append(email_info)
                    logger.info(f"✓ 邮件 {idx+1} 通过检查，已添加到处理队列")

                except Exception as e:
                    logger.error(f"解析邮件 {email_id} 失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"获取邮件失败: {e}")

        # 输出统计信息
        logger.info(f"附件统计: 总计{attachment_count}个附件, 类型分布: {dict(attachment_types)}")

        return emails

    def _decode_filename(self, filename: str) -> str:
        """解码MIME编码的文件名

        Args:
            filename: 编码的文件名

        Returns:
            解码后的文件名
        """
        if not filename:
            return filename

        # 如果是bytes类型，先转为字符串
        if isinstance(filename, bytes):
            filename = filename.decode('utf-8', errors='ignore')

        # 处理MIME编码的文件名 (=?charset?encoding?encoded-text?=)
        if '=?' in filename and '?=' in filename:
            try:
                # 使用email.header.decode_header解码
                decoded_parts = decode_header(filename)
                decoded_filename = ""
                for part, encoding in decoded_parts:
                    if isinstance(part, bytes):
                        decoded_filename += part.decode(encoding if encoding else 'utf-8', errors='ignore')
                    else:
                        decoded_filename += part
                return decoded_filename
            except:
                # 如果解码失败，返回原文件名
                return filename

        return filename

    def _is_resume_file(self, filename: str) -> bool:
        """判断是否为简历文件

        Args:
            filename: 文件名

        Returns:
            是否为简历文件
        """
        if not filename:
            return False

        # 解码文件名后再判断
        decoded_name = self._decode_filename(filename)

        # 检查文件扩展名
        resume_extensions = ('.pdf', '.PDF', '.docx', '.DOCX', '.doc', '.DOC')
        return decoded_name.endswith(resume_extensions)

    def _parse_email(self, msg: message.Message, email_id: str) -> Dict:
        """解析邮件

        Args:
            msg: 邮件对象
            email_id: 邮件ID

        Returns:
            邮件信息字典
        """
        # 解码主题
        subject = ""
        if msg["Subject"]:
            subject_parts = decode_header(msg["Subject"])
            subject = ""
            for part, encoding in subject_parts:
                if isinstance(part, bytes):
                    subject += part.decode(encoding if encoding else 'utf-8', errors='ignore')
                else:
                    subject += part

        # 解码发件人
        sender = ""
        if msg["From"]:
            sender_parts = decode_header(msg["From"])
            sender = ""
            for part, encoding in sender_parts:
                if isinstance(part, bytes):
                    sender += part.decode(encoding if encoding else 'utf-8', errors='ignore')
                else:
                    sender += part

        # 提取附件
        attachments = []
        email_body = ""

        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition')

            # 提取正文
            if content_type in ['text/plain', 'text/html'] and not content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        # 尝试多种编码
                        for encoding in ['utf-8', 'gb18030', 'gbk', 'gb2312', 'iso-8859-1']:
                            try:
                                email_body += payload.decode(encoding)
                                break
                            except:
                                continue
                        else:
                            # 如果所有编码都失败，使用errors='ignore'
                            email_body += payload.decode('utf-8', errors='ignore')
                except:
                    pass

            # 提取附件
            if content_disposition:
                file_name = part.get_filename()
                if file_name and self._is_resume_file(file_name):
                    # 解码文件名
                    decoded_filename = self._decode_filename(file_name)

                    # 只处理简历文件
                    attachments.append({
                        'filename': decoded_filename,
                        'content_type': part.get_content_type(),
                        'size': len(part.get_payload(decode=True))
                    })

        return {
            'id': email_id,
            'subject': subject,
            'sender': sender,
            'date': msg["Date"],
            'body': email_body,
            'attachments': attachments
        }

    def _should_filter_email(
        self,
        email_info: Dict,
        filter_keywords: Optional[List[str]] = None,
        sender_whitelist: Optional[List[str]] = None
    ) -> bool:
        """判断是否应该过滤该邮件

        Args:
            email_info: 邮件信息
            filter_keywords: 过滤关键词
            sender_whitelist: 发件人白名单

        Returns:
            True表示应该过滤（不处理），False表示不过滤（处理）
        """
        # 如果既没有附件也没有正文内容，过滤
        has_attachments = bool(email_info.get('attachments'))
        has_body = bool(email_info.get('body', '').strip())

        if not has_attachments and not has_body:
            return True

        # 如果有白名单，只处理白名单中的发件人
        if sender_whitelist:
            sender_match = any(
                whitelist_email in email_info['sender']
                for whitelist_email in sender_whitelist
            )
            if not sender_match:
                return True

        # 如果有关键词，检查主题是否包含关键词
        if filter_keywords:
            keyword_match = any(
                keyword.lower() in email_info['subject'].lower()
                for keyword in filter_keywords
            )
            if not keyword_match:
                return True

        return False

    def _get_filter_reason(
        self,
        email_info: Dict,
        filter_keywords: Optional[List[str]] = None,
        sender_whitelist: Optional[List[str]] = None
    ) -> str:
        """获取邮件被过滤的原因"""
        # 如果没有附件，直接过滤
        if not email_info['attachments']:
            return "没有附件"

        # 如果有白名单，只处理白名单中的发件人
        if sender_whitelist:
            sender_match = any(
                whitelist_email in email_info['sender']
                for whitelist_email in sender_whitelist
            )
            if not sender_match:
                return f"发件人不在白名单: {email_info['sender']}"

        # 如果有关键词，检查主题是否包含关键词
        if filter_keywords:
            keyword_match = any(
                keyword.lower() in email_info['subject'].lower()
                for keyword in filter_keywords
            )
            if not keyword_match:
                return f"主题不包含关键词: {filter_keywords}"

        return "未知原因"

    def download_attachment(
        self,
        email_id: str,
        file_name: str,
        save_path: str
    ) -> Optional[str]:
        """下载附件

        Args:
            email_id: 邮件ID
            file_name: 文件名（已解码）
            save_path: 保存路径

        Returns:
            保存的文件路径，失败返回None
        """
        try:
            # 获取邮件
            status, msg_data = self.client.fetch(email_id, '(RFC822)')

            if status != 'OK':
                return None

            # 解析邮件
            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email)

            # 查找并下载附件
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                attachment_file_name = part.get_filename()

                if attachment_file_name:
                    # 解码文件名
                    decoded_filename = self._decode_filename(attachment_file_name)

                    # 找到目标附件（比较解码后的文件名）
                    if decoded_filename == file_name:
                        # 保存文件（使用解码后的文件名）
                        file_path = os.path.join(save_path, file_name)
                        Path(save_path).mkdir(parents=True, exist_ok=True)

                        with open(file_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))

                        logger.info(f"附件已保存: {file_path}")
                        return file_path

            return None

        except Exception as e:
            logger.error(f"下载附件失败: {e}")
            return None

    def move_to_folder(self, email_id: str, folder_name: str) -> bool:
        """移动邮件到指定���件夹

        Args:
            email_id: 邮件ID
            folder_name: 目标文件夹名称

        Returns:
            是否成功
        """
        try:
            # 尝试移动邮件（使用COPY标记）
            self.client.copy(email_id, folder_name)
            self.client.store(email_id, '+FLAGS', '\\Seen')
            self.client.store(email_id, '+FLAGS', '\\Deleted')
            self.client.expunge()

            logger.info(f"邮件 {email_id} 已移动到 {folder_name}")
            return True

        except Exception as e:
            # 如果文件夹不存在，尝试创建后重试
            error_msg = str(e)
            if 'TRYCREATE' in error_msg or 'not found' in error_msg.lower() or 'cannot' in error_msg.lower():
                logger.warning(f"文件夹 {folder_name} 不存在，尝试创建...")
                try:
                    self.client.create(folder_name)
                    logger.info(f"成功创建文件夹 {folder_name}")

                    # 重试移动邮件
                    self.client.copy(email_id, folder_name)
                    self.client.store(email_id, '+FLAGS', '\\Seen')
                    self.client.store(email_id, '+FLAGS', '\\Deleted')
                    self.client.expunge()

                    logger.info(f"邮件 {email_id} 已移动到 {folder_name}")
                    return True
                except Exception as e2:
                    logger.error(f"创建文件夹或移动邮件失败: {e2}")
                    return False
            else:
                logger.error(f"移动邮件失败: {e}")
                return False
