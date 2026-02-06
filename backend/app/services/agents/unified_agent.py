"""统一Agent客户端 - 调用FastGPT Chat Completions API处理简历"""
import os
import json
import logging
import re
from typing import Dict, Optional, Any
import httpx

logger = logging.getLogger(__name__)


class UnifiedAgentClient:
    """统一Agent客户端

    调用FastGPT Chat Completions API，将简历（文本+PDF URL）发送给Agent处理
    返回结构化的候选人信息
    """

    def __init__(self):
        """初始化Agent客户端"""
        self.api_key = os.getenv("FASTGPT_API_KEY")
        self.base_url = os.getenv("FASTGPT_BASE_URL", "http://localhost:3000")
        self.chat_api = os.getenv("FASTGPT_CHAT_API", "/api/v1/chat/completions")
        self.timeout = int(os.getenv("FASTGPT_TIMEOUT", "120"))

    def _get_url(self) -> str:
        """获取完整的API URL"""
        return f"{self.base_url}{self.chat_api}"

    def process_resume_sync(
        self,
        title: str,
        body: str,
        pdf_url: str
    ) -> Dict[str, Any]:
        """同步方式处理简历

        Args:
            title: 邮件标题
            body: 邮件正文/简历文本
            pdf_url: PDF文件的OSS URL

        Returns:
            解析后的候选人信息字典
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "FASTGPT_API_KEY 未配置"
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构造文本内容
        text_content = f"邮件标题：{title}\n邮件正文：{body}"

        payload = {
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text_content
                        },
                        {
                            "type": "file_url",
                            "name": "resume.pdf",
                            "url": pdf_url
                        }
                    ]
                }
            ]
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self._get_url(),
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return self._parse_response(result)

        except httpx.TimeoutException:
            logger.error("Agent请求超时")
            return {
                "success": False,
                "error": "Agent请求超时"
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Agent HTTP错误: {e.response.status_code}")
            return {
                "success": False,
                "error": f"Agent HTTP错误: {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Agent调用异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_response(self, response: Dict) -> Dict[str, Any]:
        """解析Agent返回的响应

        Args:
            response: FastGPT API返回的原始响应

        Returns:
            标准化的结果字典
        """
        try:
            # FastGPT返回格式：choices[0].message.content
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]

                # 尝试解析JSON
                if isinstance(content, str):
                    # 处理markdown代码块包裹的JSON
                    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)
                    else:
                        # 尝试直接查找JSON对象
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            content = json_match.group(0)

                    parsed = json.loads(content)
                else:
                    parsed = content

                # 标准化返回格式
                # Agent可能返回 {success: true, data: {...}} 或直接返回 {...}
                if isinstance(parsed, dict) and "data" in parsed:
                    # Agent返回了包装格式
                    return parsed
                else:
                    # Agent直接返回数据
                    return {
                        "success": True,
                        "data": self._normalize_data(parsed)
                    }
            else:
                return {
                    "success": False,
                    "error": "响应格式异常：缺少choices字段"
                }

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return {
                "success": False,
                "error": f"返回内容不是有效的JSON: {e}"
            }
        except Exception as e:
            logger.error(f"响应解析异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _normalize_data(self, data: Dict) -> Dict:
        """标准化返回数据，确保所有字段都存在

        Args:
            data: Agent返回的原始数据

        Returns:
            标准化后的数据
        """
        return {
            # 基本信息
            "candidate_name": data.get("candidate_name"),
            "phone": data.get("phone"),
            "email": data.get("email"),

            # 学历信息
            "education": data.get("education"),
            "education_level": data.get("education_level"),
            "education_history": data.get("education_history", []),

            # 工作经验
            "work_years": data.get("work_years", 0),
            "work_experience": data.get("work_experience", []),

            # 项目经验
            "project_experience": data.get("project_experience", []),

            # 技能
            "skills": data.get("skills", []),

            # 地理信息
            "city": data.get("city"),

            # 职位分类
            "job_category": data.get("job_category"),

            # 评分与筛选
            "agent_score": data.get("agent_score"),
            "screening_status": data.get("screening_status", "待定"),

            # 元数据
            "evaluation_id": data.get("evaluation_id"),
            "confidence": data.get("confidence"),
            "reasoning": data.get("reasoning")
        }


# 全局单例
_agent_client: Optional[UnifiedAgentClient] = None


def get_unified_agent() -> UnifiedAgentClient:
    """获取统一Agent客户端单例"""
    global _agent_client
    if _agent_client is None:
        _agent_client = UnifiedAgentClient()
    return _agent_client
