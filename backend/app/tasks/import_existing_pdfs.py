"""导入现有的PDF文件到数据库

根据CLAUDE.md核心原则：
- 所有评分通过外部Agent完成
- 不使用本地JobMatcher进行匹配
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from pathlib import Path
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
from app.services.city_extractor import CityExtractor
from app.services.job_title_classifier import JobTitleClassifier
from app.services.agent_client import AgentClient
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 简历文件保存路径
RESUME_SAVE_PATH = '/app/resume_files'


def import_existing_pdfs():
    """扫描并导入所有现有的PDF文件"""
    db = SessionLocal()

    try:
        # 扫描PDF目录
        pdf_dir = Path(RESUME_SAVE_PATH)
        if not pdf_dir.exists():
            logger.error(f"PDF目录不存在: {RESUME_SAVE_PATH}")
            return

        pdf_files = list(pdf_dir.glob('*.pdf'))
        logger.info(f"找到 {len(pdf_files)} 个PDF文件\n")

        # 统计
        imported = 0
        skipped = 0
        failed = 0

        for idx, pdf_path in enumerate(pdf_files, 1):
            try:
                file_path = str(pdf_path)

                # 检查是否已导入
                existing = db.query(Resume).filter(Resume.file_path == file_path).first()
                if existing:
                    skipped += 1
                    if idx % 100 == 0:
                        logger.info(f"进度: {idx}/{len(pdf_files)}, 已导入: {imported}, 已跳过: {skipped}, 失败: {failed}")
                    continue

                # 1. 解析简历
                parser = ResumeParser()
                resume_data = parser.parse_resume(file_path)

                if not resume_data.get('raw_text'):
                    logger.warning(f"PDF无正文内容，跳过: {pdf_path.name}")
                    skipped += 1
                    continue

                logger.info(f"[{idx}/{len(pdf_files)}] 解析: {resume_data.get('candidate_name')} - {pdf_path.name}")

                # 2. 提取城市
                city_extractor = CityExtractor()
                city = city_extractor.extract_city(
                    email_subject='',
                    email_body='',
                    resume_text=resume_data.get('raw_text', '')
                )

                # 3. 判断职位（使用字符串匹配）
                job_classifier = JobTitleClassifier()
                job_title = job_classifier.classify_job_title(
                    email_subject='',
                    resume_text=resume_data.get('raw_text', ''),
                    skills=resume_data.get('skills', []),
                    skills_by_level=resume_data.get('skills_by_level', {})
                )

                # 4. 调用外部Agent（唯一评分来源）
                try:
                    agent_client = AgentClient()
                    agent_result = agent_client.evaluate_resume(
                        job_title=job_title,
                        city=city,
                        pdf_path=file_path,
                        resume_data=resume_data
                    )

                    # 🔴 新增：处理Agent返回None的情况（未配置FastGPT的职位）
                    if agent_result is None:
                        # 未配置FastGPT，不评分
                        agent_score = None
                        screening_status = 'pending'
                        agent_evaluated_at = None
                        logger.info(f"职位 '{job_title}' 跳过Agent评估（未配置FastGPT）")
                    else:
                        # 成功调用FastGPT
                        agent_score = agent_result['score']
                        screening_status = agent_result.get('screening_status', 'pending')
                        agent_evaluated_at = datetime.utcnow()
                        logger.info(f"Agent评分: {agent_score}")

                except Exception as e:
                    logger.warning(f"Agent评分失败: {e}")
                    agent_score = None
                    screening_status = 'pending'
                    agent_evaluated_at = None

                # 5. 保存简历到数据库
                resume = Resume(
                    candidate_name=resume_data.get('candidate_name'),
                    phone=resume_data.get('phone'),
                    email=resume_data.get('email'),
                    education=resume_data.get('education'),
                    education_level=resume_data.get('education_level'),
                    work_years=resume_data.get('work_years', 0),
                    skills=resume_data.get('skills', []),
                    skills_by_level=resume_data.get('skills_by_level', {}),
                    work_experience=resume_data.get('work_experience', []),
                    project_experience=resume_data.get('project_experience', []),
                    education_history=resume_data.get('education_history', []),
                    raw_text=resume_data.get('raw_text'),
                    file_path=file_path,
                    file_type='pdf',
                    city=city,
                    job_category=job_title,
                    pdf_path=file_path,
                    agent_score=agent_score,
                    agent_evaluated_at=agent_evaluated_at,
                    screening_status=screening_status,
                    status='processed'
                )
                db.add(resume)
                db.commit()

                imported += 1

                if imported % 10 == 0:
                    logger.info(f"  → 已成功导入 {imported} 份简历")

            except Exception as e:
                logger.error(f"导入失败 {pdf_path.name}: {e}")
                db.rollback()
                failed += 1

        # 最终统计
        logger.info("\n" + "=" * 80)
        logger.info(f"导入完成！")
        logger.info(f"  总文件数: {len(pdf_files)}")
        logger.info(f"  成功导入: {imported}")
        logger.info(f"  已存在跳过: {skipped}")
        logger.info(f"  失败: {failed}")
        logger.info("=" * 80)

        # 验证数据库
        total = db.query(Resume).count()
        valid = db.query(Resume).filter(
            Resume.file_type == 'pdf',
            Resume.raw_text.isnot(None),
            Resume.raw_text != ''
        ).count()

        logger.info(f"\n数据库验证:")
        logger.info(f"  总简历数: {total}")
        logger.info(f"  有效简历数: {valid}")

    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import_existing_pdfs()
