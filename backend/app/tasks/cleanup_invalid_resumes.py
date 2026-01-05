"""清理无效简历

根据CLAUDE.md核心原则2：只保留有正文+PDF附件的简历

删除条件（任一满足即删除）：
1. 无PDF附件（pdf_path为空）
2. 无正文内容（raw_text为空或长度为0）

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
    """清理无效简历"""
    db = SessionLocal()

    try:
        # 查找所有简历
        all_resumes = db.query(Resume).all()
        total_count = len(all_resumes)

        logger.info(f"数据库中共有 {total_count} 份简历\n")

        # 分类：有效 vs 无效
        valid_resumes = []
        invalid_resumes = []

        for resume in all_resumes:
            # 检查是否有效
            has_pdf = resume.pdf_path and resume.pdf_path != ''
            has_text = resume.raw_text and len(resume.raw_text) > 0

            if has_pdf and has_text:
                valid_resumes.append(resume)
            else:
                invalid_resumes.append({
                    'resume': resume,
                    'reason': '无PDF' if not has_pdf else ('无正文' if not has_text else '其他')
                })

        logger.info(f"有效简历: {len(valid_resumes)} 份")
        logger.info(f"无效简历: {len(invalid_resumes)} 份\n")

        if invalid_resumes:
            logger.info("无效简历列表（前10条）:")
            logger.info("-" * 80)
            for item in invalid_resumes[:10]:
                r = item['resume']
                reason = item['reason']
                logger.info(
                    f"  {r.candidate_name or '未命名'} | "
                    f"{reason} | "
                    f"pdf_path: {r.pdf_path or '空'} | "
                    f"text_len: {len(r.raw_text) if r.raw_text else 0}"
                )
            if len(invalid_resumes) > 10:
                logger.info(f"  ... 还有 {len(invalid_resumes) - 10} 条无效记录")

            # 确认删除
            logger.info(f"\n开始删除 {len(invalid_resumes)} 份无效简历...")

            deleted_count = 0
            for item in invalid_resumes:
                try:
                    resume = item['resume']

                    # 删除关联的screening_results
                    from app.models.screening_result import ScreeningResult
                    screenings = db.query(ScreeningResult).filter(
                        ScreeningResult.resume_id == resume.id
                    ).all()

                    for screening in screenings:
                        db.delete(screening)

                    # 删除简历
                    db.delete(resume)
                    db.commit()
                    deleted_count += 1

                    if deleted_count % 100 == 0 or deleted_count == len(invalid_resumes):
                        logger.info(f"  进度: {deleted_count}/{len(invalid_resumes)}")

                except Exception as e:
                    logger.error(f"  删除失败: {e}")
                    db.rollback()

            logger.info(f"\n成功删除 {deleted_count} 份无效简历")
        else:
            logger.info("没有无效简历需要删除")

        # 统计有效简历
        logger.info("\n" + "=" * 80)
        logger.info("清理完成！")
        logger.info(f"  删除: {len(invalid_resumes)} 份")
        logger.info(f"  保留: {len(valid_resumes)} 份")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"清理失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始清理无效简历...\n")
    cleanup_invalid_resumes()
