"""重新提取所有简历的教育背景

这个脚本会从原始文本中更宽松地提取教育信息
"""

import sys
import os
import re
from typing import List, Dict, Optional

# 设置Python路径
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.school_classifier import get_school_classifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_education_from_text(text: str) -> List[Dict]:
    """从原始文本中提取教育背景 - 宽松模式

    支持格式：
    1. 2011.09-2014.07 贺州学院 工程造价
    2. 2011 年 09 月-2014 年 07 月 :贺州学院 -工程造价
    3. 兰卡斯特大学 Lancaster University
       2023.10 - 2024.11
       设计管理专业/硕士
    """
    if not text:
        return []

    education_list = []

    # 学历关键词
    degree_keywords = ['博士研究生', '博士', '硕士研究生', '硕士', '本科', '大专', '专科', '高中', '中专']

    lines = text.split('\n')

    # ========== 模式1: 查找"时间范围 + 学校"模式 ==========
    # 匹配格式：2011.09-2014.07 学校名 或 2011 年 09 月-2014 年 07 月 :学校名
    time_patterns = [
        r'(\d{4})\s*年?\s*(\d{1,2})\s*月?\s*[-—至到]\s*(\d{4})\s*年?\s*(\d{1,2})\s*月?',  # 2011年09月-2014年07月
        r'(\d{4})\.(\d{1,2})\s*[-—至到]\s*(\d{4})\.(\d{1,2})',  # 2011.09-2014.07
        r'(\d{4})\s*[-—至到]\s*(\d{4})',  # 2011-2014
    ]

    for i, line in enumerate(lines):
        line = line.strip()

        # 跳过太长的行（可能是段落）
        if len(line) > 100:
            continue

        # 尝试匹配时间模式
        time_match = None
        for pattern in time_patterns:
            match = re.search(pattern, line)
            if match:
                time_match = match
                break

        if time_match:
            # 查找学校名（在同一行或后面几行）
            school = None
            degree = None
            major = None

            # 先在当前行查找学校
            # 去掉时间部分后，剩下的内容可能包含学校
            remaining_text = re.sub(time_match.group(0), '', line).strip(' :：、-—\t')

            # 检查剩余文本是否包含"大学"或"学院"
            if '大学' in remaining_text or '学院' in remaining_text:
                # 提取学校名
                for keyword in ['大学', '学院']:
                    if keyword in remaining_text:
                        idx = remaining_text.find(keyword)
                        school = remaining_text[:idx + len(keyword)]
                        # 去掉常见的前缀符号
                        school = school.strip(' :：、-—')
                        break

            # 如果当前行没找到学校，向后查找3行
            if not school:
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if '大学' in next_line or '学院' in next_line:
                        # 找到了学校
                        for keyword in ['大学', '学院']:
                            if keyword in next_line:
                                idx = next_line.find(keyword)
                                school = next_line[:idx + len(keyword)]
                                school = school.strip(' :：、-—')
                                break
                        if school:
                            break

            # 向后查找学历和专业
            for j in range(i + 1, min(i + 6, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    continue

                # 查找学历
                if not degree:
                    for deg in degree_keywords:
                        if deg in next_line:
                            degree = deg
                            break

                # 如果找到了学历，就可以停止了
                if degree:
                    break

            # 只添加找到学校的记录
            if school:
                education_list.append({
                    'school': school,
                    'degree': degree or '',
                    'major': major or '',
                    'duration': time_match.group(0)
                })

    # 如果模式1没找到，尝试模式2：直接搜索包含"大学"或"学院"的行
    if not education_list:
        for i, line in enumerate(lines):
            line = line.strip()

            # 跳过太长的行
            if len(line) > 80:
                continue

            # 查找包含"大学"或"学院"的行
            if ('大学' in line or '学院' in line) and ('工作' not in line and '公司' not in line):
                school = line.strip()

                # 向前查找时间
                duration = None
                for j in range(max(0, i - 2), i):
                    prev_line = lines[j].strip()
                    for pattern in time_patterns:
                        match = re.search(pattern, prev_line)
                        if match:
                            duration = match.group(0)
                            break
                    if duration:
                        break

                # 向后查找学历
                degree = None
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    for deg in degree_keywords:
                        if deg in next_line:
                            degree = deg
                            break
                    if degree:
                        break

                education_list.append({
                    'school': school,
                    'degree': degree or '',
                    'major': '',
                    'duration': duration or ''
                })

                # 最多取5个
                if len(education_list) >= 5:
                    break

    return education_list


def batch_re_extract_education():
    """批量重新提取教育背景"""
    db = SessionLocal()

    try:
        # 查询所有简历
        resumes = db.query(Resume).all()
        total = len(resumes)
        logger.info(f"找到 {total} 份简历需要重新提取")

        classifier = get_school_classifier()

        updated_count = 0
        no_edu_count = 0

        for idx, resume in enumerate(resumes, 1):
            try:
                # 跳过已有完整education_history的简历
                if resume.education_history and len(resume.education_history) > 0:
                    logger.debug(f"简历 {idx}/{total} 已有教育历史，跳过")
                    continue

                # 从原始文本提取教育背景
                text = resume.raw_text
                if not text:
                    no_edu_count += 1
                    continue

                education_history = extract_education_from_text(text)

                if not education_history:
                    no_edu_count += 1
                    logger.debug(f"简历 {idx}/{total} 未找到教育背景")
                    continue

                # 更新education_history
                resume.education_history = education_history

                # 判断最高学历的学校类型
                highest_edu = education_history[0]
                school_name = highest_edu.get('school', '')

                if school_name:
                    school_type = classifier.classify(school_name)
                    resume.education_level = school_type

                db.commit()
                updated_count += 1

                if idx % 100 == 0 or idx == total:
                    logger.info(
                        f"进度: {idx}/{total} | "
                        f"已更新: {updated_count} | "
                        f"无教育: {no_edu_count} | "
                        f"学校: {school_name} -> {resume.education_level}"
                    )

            except Exception as e:
                logger.error(f"处理简历 {resume.id} 时出错: {str(e)}")
                db.rollback()
                continue

        logger.info("=" * 60)
        logger.info("重新提取完成！")
        logger.info(f"总简历数: {total}")
        logger.info(f"成功更新: {updated_count}")
        logger.info(f"无教育背景: {no_edu_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"批量更新失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    batch_re_extract_education()
