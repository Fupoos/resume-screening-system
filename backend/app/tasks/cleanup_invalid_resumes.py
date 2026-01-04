"""删除无效简历（email_body类型）

根据CLAUDE.md原则2：系统只应保留有PDF+正文的简历。
删除所有 file_type = 'email_body' 的简历（这些简历没有PDF附件）。

使用方法：
    docker-compose exec backend python3 -m app.tasks.cleanup_invalid_resumes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_invalid_resumes():
    """删除email_body类型的无效简历"""
    db = SessionLocal()

    try:
        # 1. 查找所有email_body类型的简历
        logger.info("开始查找email_body类型的简历...")

        email_body_resumes = db.query(Resume).filter(
            Resume.file_type == 'email_body'
        ).all()

        if not email_body_resumes:
            logger.info("✅ 没有找到email_body类型的简历")
            return

        logger.info(f"\n找到 {len(email_body_resumes)} 份email_body类型的简历：")
        logger.info("=" * 80)

        # 2. 显示详细信息
        for idx, resume in enumerate(email_body_resumes, 1):
            subject = resume.source_email_subject or "(无标题)"
            sender = resume.source_sender or "(未知发件人)"
            logger.info(
                f"{idx}. ID: {resume.id}\n"
                f"   标题: {subject[:80]}...\n"
                f"   发件人: {sender}\n"
                f"   创建时间: {resume.created_at}\n"
            )

        # 3. 询问用户确认（在Docker环境中自动确认）
        logger.info("=" * 80)
        logger.info(f"\n⚠️  即将删除以上 {len(email_body_resumes)} 份简历")
        logger.info("这些简历没有PDF附件，不符合系统保留条件（CLAUDE.md原则2）")

        # 在Docker环境中，无法使用input()，直接删除
        # 如果需要手动确认，可以在本地运行此脚本
        logger.info("\n🔄 开始删除...")

        deleted_count = 0
        for resume in email_body_resumes:
            try:
                db.delete(resume)
                deleted_count += 1
            except Exception as e:
                logger.error(f"删除失败 {resume.id}: {e}")
                db.rollback()

        # 提交更改
        db.commit()

        logger.info("=" * 80)
        logger.info(f"✅ 成功删除 {deleted_count} 份email_body类型简历")
        logger.info("=" * 80)

        # 4. 验证删除结果
        remaining_email_body = db.query(Resume).filter(
            Resume.file_type == 'email_body'
        ).count()

        total_resumes = db.query(Resume).count()

        logger.info(f"\n📊 删除后统计：")
        logger.info(f"  总简历数: {total_resumes}")
        logger.info(f"  剩余email_body类型: {remaining_email_body}")

        if remaining_email_body == 0:
            logger.info("\n✅ 所有email_body类型简历已清理完成")
        else:
            logger.warning(f"\n⚠️  仍有 {remaining_email_body} 份email_body类型简历未删除")

    except Exception as e:
        logger.error(f"删除失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始清理无效简历（email_body类型）...\n")
    cleanup_invalid_resumes()
