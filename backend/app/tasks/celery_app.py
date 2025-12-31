"""Celery应用配置"""
from celery import Celery
from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "resume_screening",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# 显式导入任务模块以注册任务
from app.tasks import email_tasks  # noqa

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    # 定时任务配置
    beat_schedule={
        # 每5分钟检查一次新邮件（自动抓取新简历）
        'check-new-emails-every-5-minutes': {
            'task': 'app.tasks.email_tasks.check_new_emails',
            'schedule': 300.0,  # 5分钟
        },
    },
)
