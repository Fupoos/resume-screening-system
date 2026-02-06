"""统一Agent测试API"""
import os
import logging
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.agents.resume_orchestrator import ResumeOrchestrator
from app.services.agents.unified_agent import get_unified_agent
from app.services.oss_service import get_oss_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ProcessRequest(BaseModel):
    """简历处理请求"""
    title: str = "简历"
    body: str = ""
    pdf_path: str = None


class ProcessURLRequest(BaseModel):
    """简历处理请求（直接使用URL）"""
    title: str = "简历"
    body: str = ""
    pdf_url: str = ""


@router.post("/process")
def test_process(request: ProcessRequest, db: Session = Depends(get_db)):
    """测试统一处理流程

    Args:
        request: 包含 title, body, pdf_path 的请求
        db: 数据库会话

    Returns:
        处理结果
    """
    try:
        orchestrator = ResumeOrchestrator(db)
        result = orchestrator.process_resume(
            title=request.title,
            body=request.body,
            pdf_path=request.pdf_path
        )
        return result
    except Exception as e:
        logger.error(f"测试处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-url")
def test_process_url(request: ProcessURLRequest):
    """测试统一Agent（直接使用PDF URL）

    Args:
        request: 包含 title, body, pdf_url 的请求

    Returns:
        处理结果
    """
    try:
        agent = get_unified_agent()
        result = agent.process_resume_sync(
            title=request.title,
            body=request.body,
            pdf_url=request.pdf_url
        )
        return result
    except Exception as e:
        logger.error(f"测试处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-file")
async def test_process_with_file(
    title: str = "简历",
    body: str = "",
    file: UploadFile = File(...)
):
    """测试统一处理流程（上传文件）

    Args:
        title: 邮件标题
        body: 邮件正文
        file: 简历PDF文件

    Returns:
        处理结果
    """
    import tempfile
    from app.core.database import SessionLocal

    tmp_path = None
    try:
        # 保存临时文件
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # 提取文本
        if file.filename and file.filename.endswith('.pdf'):
            from app.services.resume_parser import ResumeParser
            parser = ResumeParser()
            resume_data = parser.parse_resume(tmp_path)
            if not body:
                body = resume_data.get('raw_text', '')
        else:
            # txt文件直接读取
            with open(tmp_path, 'r', encoding='utf-8') as f:
                if not body:
                    body = f.read()

        # 调用处理流程
        db = SessionLocal()
        try:
            orchestrator = ResumeOrchestrator(db)
            result = orchestrator.process_resume(
                title=title,
                body=body,
                pdf_path=tmp_path
            )
            return result
        finally:
            db.close()

    except Exception as e:
        logger.error(f"测试处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass


@router.get("/config")
def get_agent_config():
    """获取当前Agent配置信息"""
    oss_service = get_oss_service()
    agent = get_unified_agent()

    return {
        "oss": {
            "available": oss_service.is_available(),
            "bucket": os.getenv("OSS_BUCKET"),
            "endpoint": os.getenv("OSS_ENDPOINT")
        },
        "agent": {
            "api_key_configured": bool(os.getenv("FASTGPT_API_KEY")),
            "base_url": os.getenv("FASTGPT_BASE_URL"),
            "chat_api": os.getenv("FASTGPT_CHAT_API"),
            "timeout": os.getenv("FASTGPT_TIMEOUT")
        }
    }


@router.post("/test-oss-upload")
async def test_oss_upload(file: UploadFile = File(...)):
    """测试OSS上传

    Args:
        file: 要上传的文件

    Returns:
        上传结果
    """
    tmp_path = None
    try:
        # 保存临时文件
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # 上传到OSS
        oss_service = get_oss_service()
        url = oss_service.upload_file(tmp_path)

        if url:
            return {
                "success": True,
                "url": url
            }
        else:
            return {
                "success": False,
                "error": "OSS上传失败"
            }

    except Exception as e:
        logger.error(f"OSS上传测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass
