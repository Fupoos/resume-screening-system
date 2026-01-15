"""邮箱监听API - 手动触发"""
from fastapi import APIRouter, Query
from typing import Optional
from app.tasks.email_tasks import check_emails, fetch_recent_resumes

router = APIRouter()


@router.post("/trigger-check")
async def trigger_email_check():
    """手动触发邮箱检查（检查未读邮件）"""
    task = check_emails.delay()
    return {
        "message": "邮箱检查已启动",
        "task_id": task.id
    }


@router.post("/import-historical")
async def import_historical_emails(
    limit: Optional[int] = Query(1000, description="导入数量，1000表示全部导入")
):
    """批量导入历史邮件（包括已读和未读）

    Args:
        limit: 导入邮件数量，默认1000表示导入全部邮件
    """
    task = fetch_recent_resumes.delay(limit)
    return {
        "message": f"历史邮件导入已启动，目标数量: {'全部' if limit >= 1000 else limit}",
        "task_id": task.id,
        "limit": limit
    }
