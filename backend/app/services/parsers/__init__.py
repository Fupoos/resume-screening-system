"""简历解析器模块

将原有的 resume_parser.py 拆分为多个模块，提高代码可维护性。

模块结构：
- base_parser: ResumeParser主类，协调各提取器
- basic_info_extractor: 基本信息提取（姓名、电话、邮箱）
- education_extractor: 学历提取
- experience_extractor: 工作经历提取
- project_extractor: 项目经历提取
- skills_extractor: 技能提取
"""

from app.services.parsers.base_parser import ResumeParser

__all__ = ['ResumeParser']
