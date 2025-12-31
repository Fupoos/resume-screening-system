"""Agent调用服务 - 调用外部Agent进行简历评估"""
import time
import uuid
import logging
import httpx
from typing import Dict, Optional

from app.core.agent_config import get_endpoint, get_api_key, get_pdf_base_url, get_fastgpt_config

logger = logging.getLogger(__name__)


class AgentClient:
    """外部Agent客户端"""

    def __init__(self):
        """初始化Agent客户端"""
        self.api_key = get_api_key()
        self.pdf_base_url = get_pdf_base_url()
        self.fastgpt_client = None  # 延迟初始化FastGPT客户端

    def evaluate_resume(
        self,
        job_title: str,
        city: Optional[str],
        pdf_path: str,
        resume_data: dict
    ) -> dict:
        """调用外部agent进行评估

        Args:
            job_title: 具体职位（如"Java开发"）
            city: 城市名称
            pdf_path: PDF文件路径
            resume_data: 简历数据

        Returns:
            {
                "score": 85,  # 0-100
                "evaluation_id": "uuid",
                "details": {...}
            }

        Raises:
            Exception: Agent调用失败（会重试3次）
        """
        # 获取endpoint配置
        endpoint_config = get_endpoint(job_title, city)
        if not endpoint_config:
            error_msg = f"未找到职位 '{job_title}' 的Agent配置"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 根据type选择调用方式
        agent_type = endpoint_config.get("type", "http")

        if agent_type == "fastgpt":
            # 使用FastGPT进行评估
            return self._evaluate_with_fastgpt(job_title, resume_data)
        else:
            # 使用传统HTTP Agent进行评估
            return self._evaluate_with_http(endpoint_config, job_title, city, pdf_path, resume_data)

    def _evaluate_with_fastgpt(
        self,
        job_title: str,
        resume_data: dict
    ) -> dict:
        """使用FastGPT评估简历

        Args:
            job_title: 职位名称
            resume_data: 简历数据

        Returns:
            评估结果字典
        """
        try:
            # 延迟初始化FastGPT客户端
            if not self.fastgpt_client:
                config = get_fastgpt_config()
                if not config.get("api_key"):
                    raise ValueError("FastGPT API密钥未配置，请设置FASTGPT_API_KEY环境变量")

                from app.services.fastgpt_client import FastGPTClient
                self.fastgpt_client = FastGPTClient(
                    api_key=config["api_key"],
                    base_url=config["base_url"]
                )

            # 调用FastGPT
            logger.info(f"使用FastGPT评估职位: {job_title}")
            result = self.fastgpt_client.evaluate_resume(
                resume_text=resume_data.get("raw_text", ""),
                candidate_name=resume_data.get("candidate_name", ""),
                job_title=job_title
            )

            return result

        except Exception as e:
            logger.error(f"FastGPT评估失败: {str(e)}")
            # 返回默认结果（待定状态）
            return {
                "score": 50,
                "evaluation_id": str(uuid.uuid4()),
                "details": {"error": str(e)}
            }

    def _evaluate_with_http(
        self,
        endpoint_config: dict,
        job_title: str,
        city: Optional[str],
        pdf_path: str,
        resume_data: dict
    ) -> dict:
        """使用传统HTTP Agent评估简历

        Args:
            endpoint_config: endpoint配置
            job_title: 职位名称
            city: 城市名称
            pdf_path: PDF文件路径
            resume_data: 简历数据

        Returns:
            评估结果字典
        """
        # 构建请求payload
        payload = self._build_payload(job_title, city, pdf_path, resume_data)

        # 调用Agent（支持重试）
        try:
            response_data = self._call_agent_with_retry(
                endpoint_config,
                payload
            )

            # 返回结果
            return {
                "score": response_data.get("score", 0),
                "evaluation_id": response_data.get("evaluation_id", str(uuid.uuid4())),
                "details": response_data.get("details", {})
            }

        except Exception as e:
            logger.error(f"HTTP Agent调用失败: {str(e)}")
            # Agent调用失败，返回默认结果（标记为待定）
            return {
                "score": 50,  # 默认50分，标记为待定
                "evaluation_id": str(uuid.uuid4()),
                "details": {"error": str(e)}
            }

    def _build_payload(
        self,
        job_title: str,
        city: Optional[str],
        pdf_path: str,
        resume_data: dict
    ) -> dict:
        """构建Agent请求payload

        Args:
            job_title: 职位名称
            city: 城市名称
            pdf_path: PDF文件路径
            resume_data: 简历数据

        Returns:
            请求payload字典
        """
        # 生成PDF URL（相对路径转绝对路径）
        pdf_filename = pdf_path.split("/")[-1]
        pdf_url = f"{self.pdf_base_url}/resumes/{pdf_filename}"

        # 构建候选者信息
        candidate = {
            "name": resume_data.get("candidate_name", ""),
            "phone": resume_data.get("phone", ""),
            "email": resume_data.get("email", "")
        }

        # 构建payload
        payload = {
            "pdf_url": pdf_url,
            "candidate": candidate,
            "job_title": job_title,
            "city": city or "未知",
            "skills": resume_data.get("skills", []),
            "education": resume_data.get("education", ""),
            "work_years": resume_data.get("work_years", 0),
        }

        return payload

    def _call_agent_with_retry(
        self,
        endpoint_config: dict,
        payload: dict
    ) -> dict:
        """HTTP调用，支持重试（1s, 2s, 4s指数退避）

        Args:
            endpoint_config: endpoint配置 {url, timeout, retry}
            payload: 请求payload

        Returns:
            Agent响应数据

        Raises:
            Exception: 所有重试都失败后抛出异常
        """
        url = endpoint_config["url"]
        timeout = endpoint_config.get("timeout", 30)
        max_retries = endpoint_config.get("retry", 3)

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
        }

        # 添加Authorization（如果有API key）
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 重试逻辑
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"调用Agent: {url} (尝试 {attempt + 1}/{max_retries})")

                # 发送HTTP请求
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(
                        url,
                        json=payload,
                        headers=headers
                    )

                    # 检查响应状态
                    response.raise_for_status()

                    # 解析响应
                    response_data = response.json()

                    # 检查业务状态
                    if response_data.get("success", False):
                        logger.info(f"Agent调用成功: score={response_data.get('data', {}).get('score')}")
                        return response_data.get("data", {})
                    else:
                        error_msg = response_data.get("error", "Agent返回失败")
                        raise Exception(f"Agent业务错误: {error_msg}")

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Agent调用超时: {str(e)}")
            except httpx.HTTPError as e:
                last_error = e
                logger.warning(f"Agent请求失败: {str(e)}")
            except Exception as e:
                last_error = e
                logger.warning(f"Agent调用异常: {str(e)}")

            # 如果不是最后一次重试，等待后重试
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                logger.info(f"等待 {wait_time}秒后重试...")
                time.sleep(wait_time)

        # 所有重试都失败
        error_msg = f"Agent调用失败，已重试{max_retries}次: {str(last_error)}"
        logger.error(error_msg)
        raise Exception(error_msg)
