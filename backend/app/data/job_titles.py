"""职位数据库 - 用于从邮件和简历中自动判断职位类型

这是一个高可读性的配置文件，便于后续添加新职位。
每个职位包含：
- exact_patterns: 精确匹配模式（完整职位名称列表）
- fuzzy_patterns: 模糊匹配模式（正则表达式）
- required_skills: 必需技能（必须至少匹配N%）
- bonus_skills: 加分技能（提高匹配度）
- priority: 优先级（同时匹配时选高的）
- required_ratio: 必需技能最低匹配比例
"""

from typing import Dict, List, Pattern
import re


# 职位配置数据结构
JOB_TITLES: Dict[str, Dict] = {
    "Java开发": {
        "exact_patterns": [
            # 直接职位名称
            "Java开发工程师", "Java后端开发", "Java工程师", "Java后端工程师",
            "Java高级开发", "Java资深开发", "Java架构师",
            "Java软件工程师", "Java应用开发", "Java服务器开发",
            # 简称
            "Java开发", "Java后端", "Java服务端",
        ],
        "fuzzy_patterns": [
            # 正则模式（支持变体）
            r"Java.*?开发",
            r"Java.*?工程",
            r"Java.*?后端",
            r"后端.*?Java",
            r"Spring.*?开发",
            r"微服务.*?Java",
        ],
        "required_skills": [
            "Java", "Spring", "MySQL"
        ],
        "bonus_skills": [
            "Spring Boot", "Spring Cloud", "MyBatis", "Redis",
            "微服务", "Dubbo", "Nginx", "Docker", "Kubernetes",
            "分布式", "高并发", "JVM", "性能优化"
        ],
        "priority": 90,
        "required_ratio": 0.5,  # 至少匹配50%的必需技能
    },

    "销售总监": {
        "exact_patterns": [
            "销售总监", "销售经理", "大区经理", "区域销售总监",
            "销售部经理", "销售主管", "业务总监", "市场销售总监",
            "客户总监", "大客户经理", "KA经理", "销售总经理",
        ],
        "fuzzy_patterns": [
            r"销售.*?总监",
            r"销售.*?经理",
            r"业务.*?总监",
            r"大客户.*?经理",
            r"渠道.*?总监",
            r"(区域|大区).*?销售",
        ],
        "required_skills": [
            "销售", "客户开发", "团队管理", "业绩目标"
        ],
        "bonus_skills": [
            "市场", "业务", "CRM", "谈判", "客户维护",
            "渠道", "市场营销", "销售策略", "商务谈判",
            "团队建设", "目标管理", "KPI", "业绩"
        ],
        "priority": 95,
        "required_ratio": 0.6,
    },

    "自动化测试": {
        "exact_patterns": [
            "自动化测试工程师", "测试工程师", "自动化测试", "测试开发工程师",
            "软件测试工程师", "QA工程师", "SDET", "测试开发",
            "自动化测试开发", "测试架构师", "性能测试工程师",
        ],
        "fuzzy_patterns": [
            r"自动化.*?测试",
            r"测试.*?自动",
            r"测试.*?开发",
            r"QA.*?工程",
            r"性能.*?测试",
            r"接口.*?测试",
        ],
        "required_skills": [
            "自动化测试", "测试", "Selenium"
        ],
        "bonus_skills": [
            "Python", "Java", "Appium", "JMeter",
            "Postman", "REST Assured", "Pytest",
            "CI/CD", "Jenkins", "Git", "Docker",
            "性能测试", "接口测试", "JIRA", "测试用例"
        ],
        "priority": 85,
        "required_ratio": 0.5,
    },

    "市场运营": {
        "exact_patterns": [
            "市场运营", "运营经理", "市场运营专员", "运营总监",
            "市场营销", "运营策划", "品牌运营", "新媒体运营",
            "内容运营", "用户运营", "产品运营", "运营主管",
        ],
        "fuzzy_patterns": [
            r"市场.*?运营",
            r"运营.*?经理",
            r"运营.*?专员",
            r"新媒体.*?运营",
            r"(用户|产品|内容).*?运营",
            r"品牌.*?运营",
        ],
        "required_skills": [
            "市场", "运营", "营销"
        ],
        "bonus_skills": [
            "策划", "推广", "数据分析", "文案",
            "社交媒体", "新媒体", "SEO", "SEM",
            "用户增长", "活动策划", "品牌", "市场推广"
        ],
        "priority": 80,
        "required_ratio": 0.4,
    },

    "前端开发": {
        "exact_patterns": [
            "前端开发工程师", "前端工程师", "前端开发", "Web前端",
            "前端架构师", "高级前端工程师", "资深前端开发",
            "H5开发", "移动端开发", "前端页面开发",
        ],
        "fuzzy_patterns": [
            r"前端.*?开发",
            r"前端.*?工程",
            r"Web.*?前端",
            r"(React|Vue|Angular).*?开发",
            r"H5.*?开发",
            r"移动端.*?前端",
        ],
        "required_skills": [
            "JavaScript", "HTML", "CSS"
        ],
        "bonus_skills": [
            "React", "Vue", "Angular", "TypeScript",
            "Webpack", "Vite", "Node.js", "小程序",
            "移动端", "响应式", "前端工程化",
            "性能优化", "ES6", "前端架构"
        ],
        "priority": 88,
        "required_ratio": 0.5,
    },

    "产品经理": {
        "exact_patterns": [
            "产品经理", "产品专员", "产品总监", "高级产品经理",
            "资深产品经理", "产品负责人", "产品助理",
            "产品策划", "互联网产品经理", "移动产品经理",
        ],
        "fuzzy_patterns": [
            r"产品.*?经理",
            r"产品.*?总监",
            r"产品.*?专员",
            r"(互联网|移动|后台).*?产品",
            r"(高级|资深).*?产品",
        ],
        "required_skills": [
            "产品经理", "产品设计", "需求分析"
        ],
        "bonus_skills": [
            "原型", "Axure", "Figma", "数据分析",
            "用户研究", "竞品分析", "PRD", "产品规划",
            "项目管理", "沟通", "用户体验", "敏捷"
        ],
        "priority": 92,
        "required_ratio": 0.4,
    },

    "实施顾问": {
        "exact_patterns": [
            "实施顾问", "实施工程师", "软件实施", "项目实施",
            "ERP实施", "CRM实施", "系统实施", "实施专员",
            "实施经理", "技术实施", "信息化实施",
        ],
        "fuzzy_patterns": [
            r"实施.*?顾问",
            r"实施.*?工程",
            r"(ERP|CRM|OA).*?实施",
            r"软件.*?实施",
            r"项目.*?实施",
        ],
        "required_skills": [
            "实施", "项目实施"
        ],
        "bonus_skills": [
            "ERP", "CRM", "OA", "SAP", "Oracle",
            "项目管理", "客户培训", "需求调研",
            "SQL", "数据库", "沟通协调", "客户服务"
        ],
        "priority": 82,
        "required_ratio": 0.4,
    },
}


def _compile_patterns() -> Dict[str, Dict[str, List[Pattern]]]:
    """编译所有模糊匹配正则表达式

    Returns:
        {
            "职位名称": {
                "fuzzy_compiled": [pattern1, pattern2, ...]
            }
        }
    """
    compiled = {}
    for job_name, config in JOB_TITLES.items():
        compiled[job_name] = {
            "fuzzy_compiled": [
                re.compile(pattern, re.IGNORECASE)
                for pattern in config.get("fuzzy_patterns", [])
            ]
        }
    return compiled


# 预编译正则表达式（模块加载时执行）
_COMPILED_PATTERNS = _compile_patterns()


def get_job_config(job_name: str) -> Dict:
    """获取职位配置

    Args:
        job_name: 职位名称

    Returns:
        职位配置字典，如果不存在返回None
    """
    config = JOB_TITLES.get(job_name)
    if config:
        # 添加职位名称到配置中（用于后续处理）
        config["name"] = job_name
    return config


def get_all_job_names() -> List[str]:
    """获取所有职位名称列表"""
    return list(JOB_TITLES.keys())


def get_compiled_patterns(job_name: str) -> List[Pattern]:
    """获取预编译的正则表达式模式

    Args:
        job_name: 职位名称

    Returns:
        编译后的正则表达式列表
    """
    return _COMPILED_PATTERNS.get(job_name, {}).get("fuzzy_compiled", [])


def is_valid_job(job_name: str) -> bool:
    """检查职位是否在定义列表中

    Args:
        job_name: 职位名称

    Returns:
        是否为有效职位
    """
    return job_name in JOB_TITLES


# 职位类别映射（用于统计和分析）
JOB_CATEGORIES: Dict[str, str] = {
    "Java开发": "技术",
    "前端开发": "技术",
    "自动化测试": "技术",
    "销售总监": "销售",
    "市场运营": "市场",
    "产品经理": "产品",
    "实施顾问": "实施",
}


def get_job_category(job_name: str) -> str:
    """获取职位所属大类

    Args:
        job_name: 职位名称

    Returns:
        职位大类（技术/销售/市场/产品/实施）
    """
    return JOB_CATEGORIES.get(job_name, "其他")
