#!/usr/bin/env python3
"""
检查昨天新收到的邮件数量

用法:
    cd backend
    python scripts/check_yesterday_emails.py

    或指定邮箱:
    MY_EMAIL="xxx@xxx.com" MY_AUTH="your_auth_code" python scripts/check_yesterday_emails.py
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import imaplib

# 邮箱配置 (可通过环境变量覆盖)
MY_EMAIL = os.getenv('MY_EMAIL', 'es1@cloudpense.com')
MY_AUTH = os.getenv('MY_AUTH', 'bBgoF4oBr9RD7j2J')
IMAP_SERVER = 'imap.exmail.qq.com'
IMAP_PORT = 993


def check_yesterday_emails():
    """检查最近几天的邮件数量"""
    # 计算日期
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)

    # IMAP SINCE 命令要求的日期格式: DD-Jan-YYYY (如 23-Jan-2026)
    day_before_str_search = day_before.strftime('%d-%b-%Y')

    # 邮件头中的日期匹配格式 (如 "22 Jan 2026")
    day_before_str_match = day_before.strftime('%d %b %Y')
    yesterday_str_match = yesterday.strftime('%d %b %Y')
    today_str_match = today.strftime('%d %b %Y')

    print("=" * 50)
    print(f"最近3天邮件统计")
    print("=" * 50)
    print(f"邮箱: {MY_EMAIL}")
    print()
    print(f"日期:")
    print(f"  前天: {day_before.strftime('%Y-%m-%d')}")
    print(f"  昨天: {yesterday.strftime('%Y-%m-%d')}")
    print(f"  今天: {today.strftime('%Y-%m-%d')}")
    print()

    try:
        # 连接到 IMAP 服务器
        client = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        client.login(MY_EMAIL, MY_AUTH)

        # 选择文件夹
        client.select('INBOX')

        # 搜索从前天开始的所有邮件
        status, messages = client.search(None, f'SINCE {day_before_str_search}')

        if status != 'OK':
            print(f"搜索邮件失败: {status}")
            return

        email_ids = messages[0].split()

        # 统计每天的邮件数量
        before_count = 0
        yesterday_count = 0
        today_count = 0

        for email_id in email_ids:
            try:
                # 获取邮件日期
                status, msg_data = client.fetch(email_id, '(RFC822.HEADER)')
                if status == 'OK':
                    header = msg_data[0][1].decode('utf-8', errors='ignore')
                    # 解析日期行
                    for line in header.split('\n'):
                        if line.startswith('Date:'):
                            date_str = line[5:].strip()
                            if day_before_str_match in date_str:
                                before_count += 1
                            elif yesterday_str_match in date_str:
                                yesterday_count += 1
                            elif today_str_match in date_str:
                                today_count += 1
                            break
            except:
                continue

        client.close()
        client.logout()

        print(f"邮件数量:")
        print(f"  前天: {before_count} 封")
        print(f"  昨天: {yesterday_count} 封")
        print(f"  今天: {today_count} 封")
        print(f"  合计: {before_count + yesterday_count + today_count} 封")
        print("=" * 50)

    except Exception as e:
        print(f"检查邮件失败: {e}")


if __name__ == "__main__":
    check_yesterday_emails()
