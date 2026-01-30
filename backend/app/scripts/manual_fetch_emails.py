#!/usr/bin/env python3
"""
手动触发邮件提取脚本
用于手动从邮箱获取简历并解析

用法:
    python app/scripts/manual_fetch_emails.py              # 获取未读邮件
    python app/scripts/manual_fetch_emails.py --recent 50  # 获取最近50封邮件
    python app/scripts/manual_fetch_emails.py --date 2025-01-28  # 获取指定日期的邮件
    python app/scripts/manual_fetch_emails.py --no-parse   # 只获取邮件，不解析
"""
import os
import sys
import logging
import argparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='手动触发邮件提取')
    parser.add_argument('--recent', type=int, help='获取最近N封邮件')
    parser.add_argument('--date', type=str, help='获取指定日期的邮件 (格式: 2025-01-28)')
    parser.add_argument('--no-parse', action='store_true', help='只获取邮件，不解析')

    args = parser.parse_args()

    from app.services.email_service import EmailService
    from app.tasks.email_tasks import process_email, parse_resume
    from app.core.database import SessionLocal
    from app.models.resume import Resume

    # 邮箱配置（从环境变量读取）
    email_config = {
        'email_address': os.getenv('DEMO_EMAIL', 'es1@cloudpense.com'),
        'auth_code': os.getenv('DEMO_AUTH_CODE', ''),
        'imap_server': 'imap.exmail.qq.com',
        'imap_port': 993,
        'folder': 'INBOX'
    }

    if not email_config['auth_code']:
        logger.error("未配置邮箱授权码！请设置环境变量 DEMO_AUTH_CODE")
        return

    # 简历保存路径
    save_path = os.getenv('RESUME_SAVE_PATH', '/app/resume_files')
    os.makedirs(save_path, exist_ok=True)

    logger.info(f"开始从 {email_config['email_address']} 获取邮件...")

    # 创建邮箱服务
    email_service = EmailService(**email_config)

    if not email_service.connect():
        logger.error("连接邮箱失败！请检查邮箱配置")
        return

    # 根据参数选择获取模式
    emails = []

    if args.date:
        logger.info(f"正在获取 {args.date} 的邮件...")
        emails = email_service.fetch_emails_by_date(date_str=args.date, save_path=save_path)
    elif args.recent:
        logger.info(f"正在获取最近 {args.recent} 封邮件...")
        emails = email_service.fetch_recent_emails(limit=args.recent, save_path=save_path)
    else:
        # 默认获取未读邮件
        logger.info("正在获取未读邮件...")
        emails = email_service.fetch_unread_emails(save_path=save_path)

    logger.info(f"共获取到 {len(emails)} 封邮件")

    if not emails:
        logger.info("没有找到邮件")
        email_service.disconnect()
        return

    # 断开邮箱连接
    email_service.disconnect()

    # 处理每封邮件
    if args.no_parse:
        logger.info("已跳过解析 (--no-parse 参数)")
        return

    logger.info("开始处理邮件...")

    for idx, email_info in enumerate(emails):
        logger.info(f"\n处理第 {idx+1}/{len(emails)} 封邮件:")
        logger.info(f"  主题: {email_info['subject'][:50]}...")
        logger.info(f"  发件人: {email_info['sender'][:30]}...")
        logger.info(f"  附件数: {len(email_info['attachments'])}")

        # 检查是否有简历附件
        has_resume = False
        for attachment in email_info['attachments']:
            file_name = attachment['filename']
            if file_name.endswith(('.pdf', '.PDF', '.docx', '.DOCX', '.doc', '.DOC')):
                has_resume = True
                file_path = attachment.get('saved_path')
                if file_path and os.path.exists(file_path):
                    logger.info(f"  解析简历: {file_path}")
                    try:
                        # 直接调用解析逻辑
                        parse_resume(file_path, email_info)
                        logger.info(f"  ✓ 解析完成")
                    except Exception as e:
                        logger.error(f"  ✗ 解析失败: {e}")

        if not has_resume:
            logger.info(f"  无简历附件，跳过")

    logger.info("\n全部完成！")


if __name__ == "__main__":
    main()