"""修复数据库中的无效候选人名字

使用方法：
    docker-compose exec backend python3 -m app.tasks.fix_invalid_names
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import re
from app.core.database import SessionLocal
from app.models.resume import Resume
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_valid_name(name: str) -> bool:
    """检查名字是否有效"""
    if not name:
        return False

    invalid_patterns = [
        r'^[0-9a-fA-F-]{36}$',  # UUID格式

        # 常见简历标题和关键词（完整匹配或包含）
        r'实习|工作|项目|教育|技能|求职|个人|基本信息|联系方式',

        # 学历相关
        r'双一流|211|985|学士|硕士|博士|本科|大专|高中|中专',

        # 证书相关
        r'证书|资格证|获得证书|职业资格',

        # 成果相关
        r'成果|业绩|成就|工作成果|项目成果',

        # 自我评价相关
        r'自我评价|个人简介|个人总结|优势特长',

        # 其他常见无效词
        r'专业技能|专业特长|核心竞争力|主修课程|语言能力',

        # 个人属性相关
        r'身高|体重|生日|年龄|性别|民族|婚姻|健康状况|政治面貌',
        r'籍贯|出生地|现居地|现居地址|联系电话|电子邮箱|邮箱地址|电话号码',
        r'求职意向|期望薪资|到岗时间|工作性质|入职时间|从业背景',
        r'联系方式|手机号码|手机号|邮箱|邮编|通讯地址',

        # 其他常见无效词
        r'主修|外语水平|计算机能力|兴趣爱好|特长爱好',
        r'在校经历|社会实践|校园活动|获奖情况',
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, name):
            return False

    # 长度检查：1-15个字符
    if len(name) < 1 or len(name) > 15:
        return False

    # 排除纯英文（但保留中英混合）
    if re.match(r'^[a-zA-Z\s]+$', name):
        return False

    return True


def fix_invalid_names():
    """修复数据库中的无效名字"""
    db = SessionLocal()

    try:
        # 查找所有简历
        resumes = db.query(Resume).all()
        logger.info(f"总简历数: {len(resumes)}")

        fixed_count = 0
        invalid_names_examples = []

        for resume in resumes:
            if not is_valid_name(resume.candidate_name or ''):
                # 记录无效名字
                if len(invalid_names_examples) < 10:
                    invalid_names_examples.append(resume.candidate_name)

                # 将无效名字设为NULL
                logger.info(f"修复: {resume.id} - '{resume.candidate_name}' -> NULL")
                resume.candidate_name = None
                fixed_count += 1

        # 提交更改
        db.commit()

        logger.info("\n" + "=" * 80)
        logger.info(f"修复完成！")
        logger.info(f"  共修复: {fixed_count} 条记录")
        logger.info(f"  无效名字示例: {invalid_names_examples[:5]}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"修复失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始修复数据库中的无效候选人名字...\n")
    fix_invalid_names()
