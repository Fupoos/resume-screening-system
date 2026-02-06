"""Agent编排服务

协调整个简历处理流程：
1. 调用FastGPT解析Agent进行简历解析和职位分类
2. 根据职位分类路由到对应的外接评分Agent
3. 根据评分结果应用本地阈值分类
4. 保存结果到数据库
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.agent_parsing_history import AgentParsingHistory
from app.services.agents.resume_parser_agent import ResumeParserAgent
from app.services.agents.scoring_agent_router import ScoringAgentRouter
from app.services.resume_parser import ResumeParser

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Agent编排服务

    核心流程：
    解析 → 分类 → 评分 → 阈值分类 → 存储

    支持降级处理：FastGPT解析失败时回退到本地解析器
    """

    # 固定阈值
    THRESHOLD_PASS = 70  # 可以发offer
    THRESHOLD_REVIEW = 40  # 待定

    def __init__(self, db: Session, parser_api_key: str, parser_base_url: str = "https://ai.cloudpense.com/api"):
        """初始化编排服务

        Args:
            db: 数据库会话
            parser_api_key: FastGPT解析Agent的API Key
            parser_base_url: FastGPT解析Agent的基础URL
        """
        self.db = db
        self.parser_agent = ResumeParserAgent(
            api_key=parser_api_key,
            base_url=parser_base_url
        )
        self.local_parser = ResumeParser()  # 本地解析器作为降级方案

    def process_resume(
        self,
        file_path: str,
        resume_text: str,
        email_subject: Optional[str] = None,
        source_email_id: Optional[str] = None,
        source_sender: Optional[str] = None
    ) -> Dict:
        """处理简历：解析 → 分类 → 评分 → 阈值分类

        Args:
            file_path: 简历文件路径
            resume_text: 简历文本
            email_subject: 邮件主题
            source_email_id: 来源邮件ID
            source_sender: 发件人

        Returns:
            {
                "success": True/False,
                "resume": Resume对象,
                "parsed_data": {...},
                "scoring_result": {...},
                "screening_status": "pass/review/reject/pending",
                "error": "错误信息"
            }
        """
        try:
            # 步骤1: 调用FastGPT解析简历
            logger.info(f"开始使用FastGPT解析简历: {file_path}")
            parse_result = self.parser_agent.parse_resume(resume_text=resume_text)

            # 记录解析历史
            parsing_history = self._create_parsing_history(
                file_path=file_path,
                parse_result=parse_result
            )
            self.db.add(parsing_history)

            if not parse_result["success"]:
                # FastGPT解析失败，回退到本地解析
                logger.warning(f"FastGPT解析失败，回退到本地解析: {parse_result.get('error')}")
                parsed_data = self._parse_with_local_parser(resume_text, email_subject)
                parsed_data["_parse_source"] = "local"
                parsed_data["_parse_error"] = parse_result.get("error")
                parsing_history.parsing_success = False
                parsing_history.error_message = parse_result.get("error")
            else:
                parsed_data = parse_result["data"]
                parsed_data["_parse_source"] = "fastgpt"
                parsing_history.parsed_data = parsed_data
                parsing_history.parsed_candidate_name = parsed_data.get("candidate_name")
                parsing_history.parsed_job_title = parsed_data.get("matched_job_title")
                parsing_history.job_confidence = int(parsed_data.get("job_confidence", 0) * 100)

            # 步骤2: 获取职位分类
            job_title = parsed_data.get("matched_job_title", "待分类")
            job_confidence = parsed_data.get("job_confidence", 0)

            logger.info(f"简历解析完成 - 职位: {job_title}, 置信度: {job_confidence}, 解析方式: {parsed_data.get('_parse_source')}")

            # 步骤3: 根据职位路由到评分Agent
            scoring_router = ScoringAgentRouter(self.db)
            scoring_result = scoring_router.route_and_score(
                job_title=job_title,
                resume_data=parsed_data
            )

            if scoring_result is None:
                logger.warning(f"职位 {job_title} 未找到评分Agent，跳过评分")
                agent_score = None
                screening_status = "pending"
            else:
                agent_score = scoring_result["score"]
                screening_status = self._classify_by_threshold(agent_score)
                logger.info(f"评分Agent返回分数: {agent_score}, 筛选结果: {screening_status}")

            # 步骤4: 保存或更新简历
            resume = self._save_resume(
                file_path=file_path,
                parsed_data=parsed_data,
                resume_text=resume_text,
                agent_score=agent_score,
                screening_status=screening_status,
                job_title=job_title,
                job_confidence=job_confidence,
                email_subject=email_subject,
                source_email_id=source_email_id,
                source_sender=source_sender
            )

            # 更新解析历史的resume_id
            parsing_history.resume_id = resume.id
            parsing_history.processing_time_ms = parse_result.get("processing_time_ms")
            self.db.commit()

            return {
                "success": True,
                "resume": resume,
                "parsed_data": parsed_data,
                "scoring_result": scoring_result,
                "screening_status": screening_status
            }

        except Exception as e:
            logger.error(f"处理简历失败: {e}", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_with_local_parser(self, resume_text: str, email_subject: Optional[str] = None) -> Dict:
        """使用本地解析器解析简历

        Args:
            resume_text: 简历文本
            email_subject: 邮件主题

        Returns:
            解析后的数据字典
        """
        logger.info("使用本地解析器解析简历")

        # 调用本地ResumeParser
        parsed_data = self.local_parser.parse_text(
            text=resume_text,
            filename=""
        )

        # 职位分类：从邮件主题提取
        if email_subject:
            from app.services.parsers.job_title_classifier import JobTitleClassifier
            classifier = JobTitleClassifier()
            job_title = classifier.classify_from_email_subject(email_subject)
        else:
            job_title = "待分类"

        # 转换为统一格式
        return {
            "candidate_name": parsed_data.get("name", ""),
            "phone": parsed_data.get("phone", ""),
            "email": parsed_data.get("email", ""),
            "education": parsed_data.get("education", ""),
            "work_years": parsed_data.get("work_years", 0),
            "skills": parsed_data.get("skills", []),
            "work_experience": parsed_data.get("work_experience", []),
            "project_experience": parsed_data.get("project_experience", []),
            "education_history": parsed_data.get("education_history", []),
            "matched_job_title": job_title,
            "job_confidence": 0.5,  # 本地解析默认置信度
            "raw_text": resume_text
        }

    def _classify_by_threshold(self, score: int) -> str:
        """根据固定阈值分类

        Args:
            score: Agent评分 (0-100)

        Returns:
            筛选状态
        """
        if score >= self.THRESHOLD_PASS:
            return "可以发offer"
        elif score >= self.THRESHOLD_REVIEW:
            return "待定"
        else:
            return "不合格"

    def _save_resume(
        self,
        file_path: str,
        parsed_data: dict,
        resume_text: str,
        agent_score: Optional[int],
        screening_status: str,
        job_title: str,
        job_confidence: float,
        email_subject: Optional[str] = None,
        source_email_id: Optional[str] = None,
        source_sender: Optional[str] = None
    ) -> Resume:
        """保存或更新简历

        Args:
            file_path: 简历文件路径
            parsed_data: 解析后的数据
            resume_text: 简历原文
            agent_score: Agent评分
            screening_status: 筛选状态
            job_title: 职位名称
            job_confidence: 职位置信度
            email_subject: 邮件主题
            source_email_id: 来源邮件ID
            source_sender: 发件人

        Returns:
            Resume对象
        """
        # 检查是否已存在（基于姓名+手机号去重）
        candidate_name = parsed_data.get("candidate_name", "")
        phone = parsed_data.get("phone", "")

        resume = self.db.query(Resume).filter(
            Resume.candidate_name == candidate_name,
            Resume.phone == phone
        ).first()

        parse_source = parsed_data.get("_parse_source", "local")

        if resume:
            # 更新现有简历
            logger.info(f"更新现有简历: {candidate_name} ({phone})")
            resume.candidate_name = candidate_name
            resume.phone = phone
            resume.email = parsed_data.get("email", "")
            resume.education = parsed_data.get("education", "")
            resume.work_years = parsed_data.get("work_years", 0)
            resume.skills = parsed_data.get("skills", [])
            resume.work_experience = parsed_data.get("work_experience", [])
            resume.project_experience = parsed_data.get("project_experience", [])
            resume.education_history = parsed_data.get("education_history", [])
            resume.job_category = job_title
            resume.raw_text = resume_text
            resume.agent_score = agent_score
            resume.screening_status = screening_status
            resume.parsed_by_agent = parse_source
            resume.agent_parsed_at = datetime.utcnow()
            resume.agent_parsed_data = parsed_data
            resume.job_title_confidence = job_confidence
            resume.parse_success = parse_source == "fastgpt"
            resume.parse_error_message = parsed_data.get("_parse_error") if parse_source == "local" else None
            resume.status = "processed"

            if source_email_id and not resume.source_email_id:
                resume.source_email_id = source_email_id
            if email_subject and not resume.source_email_subject:
                resume.source_email_subject = email_subject
            if source_sender and not resume.source_sender:
                resume.source_sender = source_sender

        else:
            # 创建新简历
            logger.info(f"创建新简历: {candidate_name} ({phone})")

            # 确定文件类型
            file_type = "pdf" if file_path.endswith(".pdf") else "docx"

            resume = Resume(
                id=uuid.uuid4(),
                candidate_name=candidate_name,
                phone=phone,
                email=parsed_data.get("email", ""),
                education=parsed_data.get("education", ""),
                work_years=parsed_data.get("work_years", 0),
                skills=parsed_data.get("skills", []),
                work_experience=parsed_data.get("work_experience", []),
                project_experience=parsed_data.get("project_experience", []),
                education_history=parsed_data.get("education_history", []),
                job_category=job_title,
                raw_text=resume_text,
                file_path=file_path,
                file_type=file_type,
                pdf_path=file_path,
                agent_score=agent_score,
                screening_status=screening_status,
                parsed_by_agent=parse_source,
                agent_parsed_at=datetime.utcnow() if parse_source == "fastgpt" else None,
                agent_parsed_data=parsed_data if parse_source == "fastgpt" else None,
                job_title_confidence=job_confidence,
                parse_success=parse_source == "fastgpt",
                parse_error_message=parsed_data.get("_parse_error") if parse_source == "local" else None,
                source_email_id=source_email_id,
                source_email_subject=email_subject,
                source_sender=source_sender,
                status="processed"
            )
            self.db.add(resume)

        self.db.commit()
        self.db.refresh(resume)
        return resume

    def _create_parsing_history(self, file_path: str, parse_result: dict) -> AgentParsingHistory:
        """创建解析历史记录

        Args:
            file_path: 文件路径
            parse_result: 解析结果

        Returns:
            AgentParsingHistory对象
        """
        return AgentParsingHistory(
            agent_type="fastgpt",
            parsing_success=parse_result.get("success", False),
            error_message=parse_result.get("error"),
            processing_time_ms=parse_result.get("processing_time_ms")
        )
