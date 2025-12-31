"""邮箱监听API - 手动触发"""
from fastapi import APIRouter
from app.tasks.email_tasks import check_emails

router = APIRouter()


@router.post("/trigger-check")
async def trigger_email_check():
    """手动触发邮箱检查（检查未读邮件）"""
    task = check_emails.delay()
    return {
        "message": "邮箱检查已启动",
        "task_id": task.id
    }
