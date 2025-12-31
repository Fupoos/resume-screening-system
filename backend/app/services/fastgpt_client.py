"""FastGPT客户端 - 用于实施顾问职位简历评估

FastGPT是一个已经训练好的Agent，接收简历文本并返回评分
"""
import time
import uuid
import logging
import httpx
import json
from typing import Dict

logger = logging.getLogger(__name__)


class FastGPTClient:
    """FastGPT客户端 - 专门用于实施顾问简历评分"""

    def __init__(self, api_key: str, base_url: str = "https://ai.cloudpense.com/api"):
        """初始化FastGPT客户端

        Args:
            api_key: FastGPT API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = 30
        self.max_retries = 3

    def evaluate_resume(
        self,
        resume_text: str,
        candidate_name: str = "",
        job_title: str = "实施顾问"
    ) -> Dict:
        """评估简历并返回分数

        Args:
            resume_text: 简历原始文本
            candidate_name: 候选人姓名
            job_title: 职位名称

        Returns:
            {
                "score": 85,  # 0-100分
                "evaluation_id": "uuid",
                "details": {}  # FastGPT返回的详细信息
            }
        """
        # 构建提示词（简洁版，因为FastGPT已经训练好）
        prompt = self._build_prompt(resume_text, candidate_name, job_title)

        # 调用FastGPT API
        try:
            response_text = self._call_fastgpt_with_retry(prompt)

            # 解析响应
            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"FastGPT评估失败: {str(e)}")
            # 返回默认评估（待定状态）
            return {
                "score": 50,
                "evaluation_id": str(uuid.uuid4()),
                "details": {"error": str(e)}
            }

    def _build_prompt(
        self,
        resume_text: str,
        candidate_name: str,
        job_title: str
    ) -> str:
        """构建发送给FastGPT的提示词

        Args:
            resume_text: 简历文本
            candidate_name: 候选人姓名
            job_title: 职位名称

        Returns:
            提示词字符串
        """
        # 限制简历长度，避免超出token限制
        resume_text = resume_text[:3000]

        prompt = f"""请评估以下候选人是否适合{job_title}职位。

候选人姓名: {candidate_name}

简历内容:
{resume_text}

请只返回一个0-100的数字评分，不要包含任何其他文字。
评分标准：
- 90-100分: 完全匹配，可以立即发offer
- 70-89分: 基本匹配，可以考虑发offer
- 50-69分: 部分匹配，需要进一步评估
- 0-49分: 不匹配，不建议面试
"""
        return prompt

    def _call_fastgpt_with_retry(self, prompt: str) -> str:
        """调用FastGPT API，支持重试

        Args:
            prompt: 提示词

        Returns:
            FastGPT响应文本

        Raises:
            Exception: 所有重试都失败后抛出异常
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 生成唯一的chatId
        chat_id = f"resume_eval_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        payload = {
            "chatId": chat_id,
            "stream": False,
            "detail": False,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"调用FastGPT API (尝试 {attempt + 1}/{self.max_retries})")

                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        url,
                        json=payload,
                        headers=headers
                    )

                    response.raise_for_status()
                    response_data = response.json()

                    # 提取回复内容
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        message = response_data["choices"][0].get("message", {})
                        content = message.get("content", "")
                        logger.info(f"FastGPT调用成功，响应长度: {len(content)}")
                        return content
                    else:
                        raise Exception("FastGPT响应格式错误: 缺少choices字段")

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"FastGPT调用超时: {str(e)}")
            except httpx.HTTPError as e:
                last_error = e
                logger.warning(f"FastGPT请求失败: {str(e)}")
            except Exception as e:
                last_error = e
                logger.warning(f"FastGPT调用异常: {str(e)}")

            # 如果不是最后一次重试，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                logger.info(f"等待 {wait_time}秒后重试...")
                time.sleep(wait_time)

        # 所有重试都失败
        error_msg = f"FastGPT调用失败，已重试{self.max_retries}次: {str(last_error)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def _parse_response(self, response: str) -> Dict:
        """解析FastGPT的响应

        Args:
            response: FastGPT返回的文本

        Returns:
            评估结果字典
        """
        try:
            # 清理响应文本
            response = response.strip()

            # 尝试提取数字（支持多种格式）
            # 格式1: 纯数字 "85"
            # 格式2: 带文字 "评分: 85"
            # 格式3: JSON格式 {"score": 85}

            # 先尝试JSON解析
            if response.startswith("{"):
                try:
                    result = json.loads(response)
                    if "score" in result:
                        score = int(result["score"])
                    else:
                        score = 50
                except:
                    score = 50
            else:
                # 提取数字
                import re
                match = re.search(r'\b(\d{1,3})\b', response)
                if match:
                    score = int(match.group(1))
                else:
                    logger.warning(f"无法从响应中提取评分: {response[:100]}")
                    score = 50

            # 确保分数在0-100范围内
            score = max(0, min(100, score))

            return {
                "score": score,
                "evaluation_id": str(uuid.uuid4()),
                "details": {"raw_response": response[:500]}  # 保存原始响应（前500字符）
            }

        except Exception as e:
            logger.error(f"解析FastGPT响应失败: {str(e)}")
            return {
                "score": 50,
                "evaluation_id": str(uuid.uuid4()),
                "details": {"error": str(e)}
            }

    def test_connection(self) -> bool:
        """测试FastGPT连接

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "chatId": f"test_{int(time.time())}",
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": "你好，请回复数字100"
                    }
                ]
            }

            with httpx.Client(timeout=10) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

            logger.info("FastGPT连接测试成功")
            return True

        except Exception as e:
            logger.error(f"FastGPT连接测试失败: {str(e)}")
            return False
