"""邮箱配置服务 - 统一管理邮箱配置和EmailService创建"""
import os
from typing import Dict, Optional
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class EmailConfigService:
    """邮箱配置服务 - 统一管理邮箱配置和EmailService实例创建

    用途：
    - 统一获取邮箱配置（从环境变量）
    - 统一创建EmailService实例
    - 避免在多处重复相同的配置获取和实例创建代码
    """

    @staticmethod
    def get_config() -> Dict[str, any]:
        """获取邮箱配置（从环境变量）

        Returns:
            邮箱配置字典，包含：
            - email_address: 邮箱地址
            - auth_code: 授权码
            - imap_server: IMAP服务器
            - imap_port: IMAP端口
            - folder: 文件夹名称
        """
        return {
            'email_address': os.getenv('DEMO_EMAIL', ''),
            'auth_code': os.getenv('DEMO_AUTH_CODE', ''),
            'imap_server': os.getenv('DEFAULT_IMAP_SERVER', 'imap.exmail.qq.com'),
            'imap_port': int(os.getenv('DEFAULT_IMAP_PORT', '993')),
            'folder': 'INBOX'
        }

    @classmethod
    def create_service(cls, config: Optional[Dict] = None) -> Optional[EmailService]:
        """创建EmailService实例

        Args:
            config: 邮箱配置字典，如果为None则使用默认配置

        Returns:
            EmailService实例，如果配置无效则返回None
        """
        if config is None:
            config = cls.get_config()

        if not config.get('auth_code'):
            logger.warning("未配置邮箱授权码，无法创建EmailService")
            return None

        return EmailService(
            email_address=config['email_address'],
            auth_code=config['auth_code'],
            imap_server=config['imap_server'],
            imap_port=config['imap_port'],
            folder=config['folder']
        )

    @classmethod
    def is_configured(cls) -> bool:
        """检查邮箱是否已配置

        Returns:
            True如果已配置授权码，否则False
        """
        config = cls.get_config()
        return bool(config.get('auth_code'))
