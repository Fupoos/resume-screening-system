"""智能重试提取候选人姓名（V2改进版）

对于 candidate_name 为 NULL 且有PDF的简历，
使用改进后的提取逻辑重新尝试提取姓名。

改进内容：
1. 支持带空格的姓名格式（如"李 晓 斌"）
2. 优化文件名提取逻辑（支持更多格式）
3. 扩大正文搜索范围

使用方法：
    docker-compose exec backend python3 -m app.tasks.retry_extract_names_v2
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry_extract_names_v2():
    """智能重试提取候选人姓名（V2改进版）"""
    db = SessionLocal()

    try:
        # 1. 查找所有 candidate_name 为 NULL 且有PDF的简历
        logger.info("开始查找需要重试提取的简历...")

        null_name_with_pdf = db.query(Resume).filter(
            Resume.candidate_name.is_(None),
            Resume.file_type == 'pdf',
            Resume.pdf_path.isnot(None)
        ).all()

        if not null_name_with_pdf:
            logger.info("✅ 没有找到需要重试提取的简历")
            return

        logger.info(f"\n找到 {len(null_name_with_pdf)} 份需要重试提取的简历\n")

        # 2. 初始化解析器
        parser = ResumeParser()

        # 统计
        success_count = 0
        failed_count = 0

        # 3. 逐个处理
        for idx, resume in enumerate(null_name_with_pdf, 1):
            filename = os.path.basename(resume.pdf_path) if resume.pdf_path else 'N/A'

            logger.info(
                f"[{idx}/{len(null_name_with_pdf)}] 处理简历: "
                f"filename={filename}"
            )

            # 检查是否有 raw_text
            if not resume.raw_text:
                logger.warning(f"  ⚠️  简历没有正文内容，跳过")
                failed_count += 1
                continue

            # 尝试重新提取姓名（使用改进的逻辑）
            try:
                # 优先级1: 从邮件标题提取姓名
                new_name = None
                if resume.source_email_subject:
                    new_name = parser._extract_name_from_email_subject(
                        resume.source_email_subject
                    )
                    if new_name:
                        logger.info(f"  ✅ 成功（从邮件标题）: {new_name}")

                # 优先级2: 从文件名提取姓名（使用改进的逻辑）
                if not new_name and resume.pdf_path:
                    new_name = parser._extract_name_from_filename(
                        resume.pdf_path
                    )
                    if new_name:
                        logger.info(f"  ✅ 成功（从文件名）: {new_name}")

                # 优先级3: 从简历正文提取姓名（使用改进的逻辑）
                if not new_name:
                    new_name = parser._extract_name(resume.raw_text)
                    if new_name:
                        logger.info(f"  ✅ 成功（从正文）: {new_name}")

                # 更新数据库
                if new_name:
                    resume.candidate_name = new_name
                    db.commit()
                    success_count += 1
                else:
                    logger.warning(f"  ❌ 失败（无法提取有效姓名），保持NULL")
                    failed_count += 1

            except Exception as e:
                logger.error(f"  ⚠️  处理失败: {e}")
                db.rollback()
                failed_count += 1

        # 4. 输出统计
        logger.info("\n" + "=" * 80)
        logger.info(f"重试提取完成！")
        logger.info(f"  成功提取: {success_count} 份")
        logger.info(f"  失败（保持NULL）: {failed_count} 份")
        logger.info(f"  总计: {len(null_name_with_pdf)} 份")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"重试提取失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始智能重试提���候选人姓名（V2改进版）...\n")
    retry_extract_names_v2()
