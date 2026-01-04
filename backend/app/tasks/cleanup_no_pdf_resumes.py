"""删除无PDF文件的简历

根据CLAUDE.md原则2：系统只应保留有PDF+正文的简历。
删除所有 pdf_path 为 NULL 或 raw_text 为空的简历。

使用方法：
    docker-compose exec backend python3 -m app.tasks.cleanup_no_pdf_resumes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_no_pdf_resumes():
    """删除无PDF文件或无正文的无效简历"""
    db = SessionLocal()

    try:
        # 1. 查找所有无PDF或无正文的简历
        logger.info("开始查找无PDF或无正文的简历...")

        invalid_resumes = db.query(Resume).filter(
            (Resume.pdf_path.is_(None)) | (Resume.raw_text.is_(None)) | (Resume.raw_text == '')
        ).all()

        if not invalid_resumes:
            logger.info("✅ 没有找到无PDF或无正文的简历")
            return

        logger.info(f"\n找到 {len(invalid_resumes)} 份无PDF或无正文的简历：")
        logger.info("=" * 80)

        # 2. 显示详细信息
        for idx, resume in enumerate(invalid_resumes, 1):
            filename = os.path.basename(resume.file_path or 'N/A') if resume.file_path else 'N/A'
            subject = resume.source_email_subject or "(无标题)"
            logger.info(
                f"{idx}. ID: {resume.id}\n"
                f"   文件名: {filename}\n"
                f"   邮件标题: {subject[:60]}...\n"
                f"   pdf_path: {resume.pdf_path or 'NULL'}\n"
                f"   raw_text长度: {len(resume.raw_text) if resume.raw_text else 0}\n"
            )

        # 3. 确认删除
        logger.info("=" * 80)
        logger.info(f"\n⚠️  即将删除以上 {len(invalid_resumes)} 份简历")
        logger.info("这些简历没有PDF文件或正文内容，不符合系统保留条件（CLAUDE.md原则2）")

        logger.info("\n🔄 开始删除...")

        deleted_count = 0
        for resume in invalid_resumes:
            try:
                db.delete(resume)
                deleted_count += 1
            except Exception as e:
                logger.error(f"删除失败 {resume.id}: {e}")
                db.rollback()

        # 提交更改
        db.commit()

        logger.info("=" * 80)
        logger.info(f"✅ 成功删除 {deleted_count} 份无PDF或无正文的简历")
        logger.info("=" * 80)

        # 4. 验证删除结果
        remaining_invalid = db.query(Resume).filter(
            (Resume.pdf_path.is_(None)) | (Resume.raw_text.is_(None)) | (Resume.raw_text == '')
        ).count()

        total_resumes = db.query(Resume).count()

        logger.info(f"\n📊 删除后统计：")
        logger.info(f"  总简历数: {total_resumes}")
        logger.info(f"  剩余无PDF或无正文: {remaining_invalid}")

        if remaining_invalid == 0:
            logger.info("\n✅ 所有无效简历已清理完成")
        else:
            logger.warning(f"\n⚠️  仍有 {remaining_invalid} 份无效简历未删除")

    except Exception as e:
        logger.error(f"删除失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始清理无PDF或无正文的简历...\n")
    cleanup_no_pdf_resumes()
