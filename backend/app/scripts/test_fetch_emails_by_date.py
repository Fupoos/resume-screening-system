"""测试脚本：获取指定日期的邮件"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.email_service import EmailService


def main():
    # 邮箱配置（从环境变量读取，或直接填入）
    email_address = os.getenv('DEMO_EMAIL', 'es1@cloudpense.com')
    auth_code = os.getenv('DEMO_AUTH_CODE', '')

    if not auth_code:
        print("错误：未设置邮箱授权码")
        print("请设置环境变量 DEMO_AUTH_CODE，或直接修改脚本中的 auth_code")
        return

    # 日期（可修改）
    date_str = '2026-01-21'

    print(f"正在获取 {date_str} 的邮件...")
    print(f"邮箱: {email_address}")
    print("-" * 60)

    # 创建邮箱服务
    email_service = EmailService(
        email_address=email_address,
        auth_code=auth_code,
        imap_server='imap.exmail.qq.com',
        imap_port=993,
        folder='INBOX'
    )

    try:
        # 获取指定日期的邮件
        emails = email_service.fetch_emails_by_date(date_str)

        print(f"\n找到 {len(emails)} 封邮件\n")

        for idx, email in enumerate(emails, 1):
            print(f"{idx}. 主题: {email['subject'][:60]}")
            print(f"   发件人: {email['sender'][:40]}")
            print(f"   日期: {email['date']}")
            print(f"   附件: {len(email['attachments'])} 个")
            if email['attachments']:
                for att in email['attachments']:
                    print(f"      - {att['filename']} ({att['size']} bytes)")
            print()

        # 统计附件
        total_attachments = sum(len(e['attachments']) for e in emails)
        pdf_count = sum(
            1 for e in emails
            for att in e['attachments']
            if att['filename'].lower().endswith('.pdf')
        )
        docx_count = sum(
            1 for e in emails
            for att in e['attachments']
            if att['filename'].lower().endswith('.docx')
        )

        print("=" * 60)
        print(f"统计: {len(emails)} 封邮件, {total_attachments} 个附件")
        print(f"      PDF: {pdf_count} 个, DOCX: {docx_count} 个")

    finally:
        email_service.disconnect()


if __name__ == '__main__':
    main()
