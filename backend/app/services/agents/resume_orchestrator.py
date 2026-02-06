"""简历处理编排器

简化流程：
1. 上传PDF到阿里云OSS
2. 调用统一Agent API处理
3. 返回结构化数据
"""
import logging
import time
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.services.oss_service import get_oss_service
from app.services.agents.unified_agent import get_unified_agent

logger = logging.getLogger(__name__)


class ResumeOrchestrator:
    """简历处理编排器

    简化的单阶段处理流程：
    1. 上传PDF到OSS获取URL
    2. 调用统一Agent API（传入邮件标题、正文、PDF URL）
    3. Agent返回所有结构化数据（打分+关键字段）
    """

    def __init__(self, db: Session):
        """初始化编排器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.oss_service = get_oss_service()
        self.agent = get_unified_agent()

    def process_resume(
        self,
        title: str,
        body: str,
        pdf_path: Optional[str] = None
    ) -> Dict:
        """处理简历

        Args:
            title: 邮件标题
            body: 邮件正文/简历文本
            pdf_path: PDF文件路径（可选）

        Returns:
            {
                "success": True/False,
                "data": {...},  # Agent返回的结构化数据
                "error": "错误信息",
                "processing_details": {
                    "oss_upload_success": True,
                    "oss_upload_time_ms": 123,
                    "agent_call_success": True,
                    "agent_call_time_ms": 1234,
                    "pdf_url": "https://..."
                }
            }
        """
        processing_details = {
            "oss_upload_success": False,
            "oss_upload_time_ms": 0,
            "agent_call_success": False,
            "agent_call_time_ms": 0,
            "pdf_url": None
        }

        # ===== 阶段 1: 上传PDF到OSS =====
        pdf_url = None
        if pdf_path:
            start_time = time.time()
            try:
                logger.info(f"上传PDF到OSS: {pdf_path}")
                pdf_url = self.oss_service.upload_file(pdf_path)
                processing_details["oss_upload_time_ms"] = int((time.time() - start_time) * 1000)

                if pdf_url:
                    processing_details["oss_upload_success"] = True
                    processing_details["pdf_url"] = pdf_url
                    logger.info(f"OSS上传成功: {pdf_url}")
                else:
                    logger.warning("OSS上传失败，将不传递PDF URL给Agent")

            except Exception as e:
                logger.error(f"OSS上传异常: {e}")

        # ===== 阶段 2: 调用统一Agent =====
        start_time = time.time()
        try:
            logger.info("调用统一Agent处理简历")
            result = self.agent.process_resume_sync(
                title=title,
                body=body,
                pdf_url=pdf_url or ""
            )

            processing_details["agent_call_time_ms"] = int((time.time() - start_time) * 1000)

            if result.get("success"):
                processing_details["agent_call_success"] = True
                logger.info("Agent处理成功")
                return {
                    "success": True,
                    "data": result.get("data"),
                    "processing_details": processing_details
                }
            else:
                logger.error(f"Agent处理失败: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Agent处理失败"),
                    "processing_details": processing_details
                }

        except Exception as e:
            logger.error(f"Agent调用异常: {e}")
            processing_details["agent_call_time_ms"] = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "error": f"Agent调用异常: {str(e)}",
                "processing_details": processing_details
            }


def get_resume_orchestrator(db: Session) -> ResumeOrchestrator:
    """获取简历编排器实例

    Args:
        db: 数据库会话

    Returns:
        ResumeOrchestrator实例
    """
    return ResumeOrchestrator(db)
