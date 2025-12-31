"""外部Agent配置

用于根据具体职位和城市路由到对应的外部Agent评估服务
"""

import os
from typing import Dict, Optional


# Agent endpoint配置
# 格式：{职位_城市: {url, timeout, retry}}
AGENT_ENDPOINTS: Dict[str, Dict] = {
    # 精确匹配（具体职位_城市）
    # 示例配置（实际使用时需要替换为真实的Agent endpoint）
    # "Java开发_北京": {
    #     "url": "https://api.example.com/java-beijing",
    #     "timeout": 30,
    #     "retry": 3
    # },

    # 默认endpoint（fallback）
    "Java开发_default": {
        "url": os.getenv("AGENT_JAVA_URL", "https://api.example.com/java"),
        "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
        "retry": int(os.getenv("AGENT_RETRY_COUNT", "3")),
    },
    "销售总监_default": {
        "url": os.getenv("AGENT_SALES_URL", "https://api.example.com/sales-director"),
        "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
        "retry": int(os.getenv("AGENT_RETRY_COUNT", "3")),
    },
    "自动化测试_default": {
        "url": os.getenv("AGENT_TEST_URL", "https://api.example.com/automation-test"),
        "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
        "retry": int(os.getenv("AGENT_RETRY_COUNT", "3")),
    },
    "市场运营_default": {
        "url": os.getenv("AGENT_MARKETING_URL", "https://api.example.com/marketing"),
        "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
        "retry": int(os.getenv("AGENT_RETRY_COUNT", "3")),
    },
    "前端开发_default": {
        "url": os.getenv("AGENT_FRONTEND_URL", "https://api.example.com/frontend"),
        "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
        "retry": int(os.getenv("AGENT_RETRY_COUNT", "3")),
    },
    "产品经理_default": {
        "url": os.getenv("AGENT_PRODUCT_URL", "https://api.example.com/product-manager"),
        "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
        "retry": int(os.getenv("AGENT_RETRY_COUNT", "3")),
    },
    "实施顾问_default": {
        "url": os.getenv("AGENT_IMPLEMENTATION_URL", "https://api.example.com/implementation"),
        "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
        "retry": int(os.getenv("AGENT_RETRY_COUNT", "3")),
    },
}


def get_endpoint(job_title: str, city: Optional[str] = None) -> Optional[Dict]:
    """获取endpoint配置，优先精确匹配，fallback到default

    Args:
        job_title: 具体职位（如"Java开发"）
        city: 城市名称（如"北京"）

    Returns:
        endpoint配置字典 {url, timeout, retry}
        如果未找到配置返回None
    """
    if city:
        # 优先尝试精确匹配（职位_城市）
        exact_key = f"{job_title}_{city}"
        if exact_key in AGENT_ENDPOINTS:
            return AGENT_ENDPOINTS[exact_key]

    # Fallback到默认endpoint
    default_key = f"{job_title}_default"
    return AGENT_ENDPOINTS.get(default_key)


def get_api_key() -> str:
    """获取Agent API密钥

    Returns:
        API密钥字符串
    """
    return os.getenv("AGENT_API_KEY", "")


def get_pdf_base_url() -> str:
    """获取PDF基础URL（用于生成可访问的PDF URL）

    Returns:
        PDF基础URL
    """
    return os.getenv("PDF_BASE_URL", "https://your-server.com")
