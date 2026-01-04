"""检查PDF文件存在性

检查所有简历的PDF文件是否存在，生成详细报告。

使用方法：
    docker-compose exec backend python3 -m app.tasks.check_pdf_files

输出：
    - 控制台：统计信息
    - 文件：/tmp/pdf_check_report.csv
"""
import sys
import os
import csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import SessionLocal
from app.models.resume import Resume
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 报告文件路径
REPORT_FILE = "/tmp/pdf_check_report.csv"


def check_pdf_files():
    """检查所有简历的PDF文件是否存在"""
    db = SessionLocal()

    try:
        # 1. 获取所有PDF简历
        logger.info("开始检查PDF文件...")

        all_resumes = db.query(Resume).filter(
            Resume.file_type == 'pdf'
        ).all()

        logger.info(f"找到 {len(all_resumes)} 份PDF简历\n")

        # 2. 检查文件存在性
        missing_files = []  # pdf_path不为空但文件不存在
        never_generated = []  # pdf_path为空（从未生成）
        valid_files = []  # 文件存在

        for resume in all_resumes:
            # 优先使用pdf_path，如果为空才使用file_path
            pdf_path = resume.pdf_path or resume.file_path

            if not pdf_path:
                # 从未生成PDF
                never_generated.append(resume)
            elif not os.path.exists(pdf_path):
                # PDF路径存在但文件丢失
                missing_files.append(resume)
            else:
                # 文件存在
                valid_files.append(resume)

        # 3. 输出统计
        logger.info("=" * 80)
        logger.info(f"检查完成！")
        logger.info(f"  总简历数: {len(all_resumes)}")
        logger.info(f"  文件存在: {len(valid_files)} 份")
        logger.info(f"  文件丢失: {len(missing_files)} 份")
        logger.info(f"  未生成PDF: {len(never_generated)} 份")
        logger.info("=" * 80)

        # 4. 生成详细报告（CSV）
        with open(REPORT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow([
                'resume_id', 'candidate_name', 'file_path', 'pdf_path',
                'status', 'note'
            ])

            # 写入文件丢失的记录
            for resume in missing_files:
                pdf_path = resume.pdf_path or resume.file_path
                writer.writerow([
                    str(resume.id),
                    resume.candidate_name or 'NULL',
                    resume.file_path or 'NULL',
                    resume.pdf_path or 'NULL',
                    'missing',
                    f'文件不存在: {pdf_path}'
                ])

            # 写入未生成PDF的记录
            for resume in never_generated:
                writer.writerow([
                    str(resume.id),
                    resume.candidate_name or 'NULL',
                    resume.file_path or 'NULL',
                    resume.pdf_path or 'NULL',
                    'never_generated',
                    'pdf_path为空'
                ])

            # 写入文件存在的记录（可选，用于验证）
            for resume in valid_files[:10]:  # 只写前10条作为样本
                pdf_path = resume.pdf_path or resume.file_path
                writer.writerow([
                    str(resume.id),
                    resume.candidate_name or 'NULL',
                    resume.file_path or 'NULL',
                    resume.pdf_path or 'NULL',
                    'valid',
                    pdf_path
                ])

        logger.info(f"\n📄 详细报告已保存到: {REPORT_FILE}")
        logger.info(f"   报告包含 {len(missing_files) + len(never_generated)} 条问题记录")

        # 5. 显示前10条问题记录
        if missing_files or never_generated:
            logger.info("\n前10条问题记录:")
            logger.info("-" * 80)

            problem_resumes = (missing_files + never_generated)[:10]
            for idx, resume in enumerate(problem_resumes, 1):
                pdf_path = resume.pdf_path or resume.file_path
                status = 'missing' if resume in missing_files else 'never_generated'
                logger.info(
                    f"{idx}. {resume.candidate_name or 'NULL'} - "
                    f"status={status}, path={pdf_path or 'NULL'}"
                )

            logger.info("-" * 80)

            if len(missing_files) + len(never_generated) > 10:
                logger.info(f"... 还有 {len(missing_files) + len(never_generated) - 10} 条记录")
                logger.info(f"请查看完整报告: {REPORT_FILE}")

    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_pdf_files()
