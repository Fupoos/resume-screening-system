"""智能重试提取候选人姓名

对于被错误识别为字段标签的简历（如"性别"、"手机"等），
尝试使用更严格的逻辑重新提取正确的姓名。

使用方法：
    docker-compose exec backend python3 -m app.tasks.retry_extract_names
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


# 无效名字黑名单（与resume_parser.py保持一致）
INVALID_NAMES = {
    # 标题类
    '教育背景', '基本信息', '个人优势', '工作经历', '项目经验',
    '求职意向', '教育经历', '专业技能', '自我评价', '联系方式',
    '个人简历', '简历', '姓名', '名字', '候选人', '应聘',
    '求职信息', '出生年月', '政治面貌', '工作年限',
    '个人信息', '个人总结', '个人简介', '个人评价', '优势亮点',
    '掌握技能', '资格证书',
    # 常见字段标签
    '性别', '手机', '电话', '邮箱', '出生日期', '出生年月', '年龄',
    '籍贯', '地址', '婚姻状况', '民族', '现居住地', '通讯地址',
    '邮政编码', '最高学历', '期望薪资', '期望城市', '应聘岗位',
    '男', '女',
    # 学历
    '本科', '硕士', '博士', '大专', '专科', '高中', '中专',
    '专升本', '研究生', '双一流',
    # 城市
    '上海', '北京', '深圳', '广州', '杭州', '成都', '武汉',
    # 🔴 新增第二轮：补充无效名字
    '同学', '微信号', '手机号', '先生', '女士', '小姐',
    # 🔴 新增第三轮：更多字段标签
    '出生年日', '工作时长', '联系电话', '现所在地', '相关课程',
    '项目描述', '发件人', '实习留用', '综合绩点', '手机号码',
    '学校住址', '工作地点', '居住地址', '户籍地址', '电子邮箱',
    '主修专业', '所学专业', '专业名称',
    # 🔴 新增：常见专业名称（这些被误识别为姓名）
    '应用化学', '计算机', '财务管理', '市场营销', '工商管理',
    '信息管理', '软件技术', '网络工程', '电子信息', '机械设计',
    '土木工程', '材料科学', '生物工程', '环境工程', '化学工程',
    # 🔴 新增第四轮：更多无效提取结果
    '意向城市', '户籍', '现居城市', '毕业院校', '英语水平',
    '英语', '产品运营', '费用报销', '发送时间', '发送日期', '后端开发',
    '前端开发', '测试开发', '运营管理', '项目管理', '系统架构',
    '���据分析', '数据管理', '技术支持', '软件开发', '系统设计',
    # 🔴 新增第五轮：更多字段标签
    '收件人', '客户成功', '求职类型', '业务支持', '客户服务',
    '售后服务', '销售支持', '市场支持', '运营支持', '技术总监',
    '产品总监', '运营总监', '销售经理', '市场经理', '项目经理',
    # 🔴 新增第六轮：最后清理
    '主题', '培训赋能', '主题名称', '邮件主题', '附件说明',
}


def retry_extract_names():
    """智能重试提取候选人姓名"""
    db = SessionLocal()

    try:
        # 1. 查找所有无效名字的简历
        logger.info("开始查找无效名字的简历...")

        invalid_resumes = db.query(Resume).filter(
            Resume.candidate_name.in_(INVALID_NAMES)
        ).all()

        if not invalid_resumes:
            logger.info("✅ 没有找到需要修复的简历")
            return

        logger.info(f"找到 {len(invalid_resumes)} 份需要修复的简历\n")

        # 2. 初始化解析器
        parser = ResumeParser()

        # 统计
        success_count = 0
        failed_count = 0
        skipped_count = 0

        # 3. 逐个处理
        for idx, resume in enumerate(invalid_resumes, 1):
            old_name = resume.candidate_name
            logger.info(
                f"[{idx}/{len(invalid_resumes)}] 处理简历: "
                f"旧名字='{old_name}', 文件={os.path.basename(resume.file_path or 'N/A')}"
            )

            # 检查是否有raw_text
            if not resume.raw_text:
                logger.warning(f"  ⚠️  简历没有正文内容，跳过")
                skipped_count += 1
                continue

            # 尝试重新提取姓名
            try:
                # 优先级1: 从邮件标题提取
                if resume.source_email_subject:
                    new_name = parser._extract_name_from_email_subject(
                        resume.source_email_subject
                    )
                    if new_name and new_name not in INVALID_NAMES:
                        resume.candidate_name = new_name
                        db.commit()
                        success_count += 1
                        logger.info(f"  ✅ 成功（从邮件标题）: {old_name} → {new_name}")
                        continue

                # 优先级2: 从文件名提取
                if resume.file_path:
                    new_name = parser._extract_name_from_filename(
                        resume.file_path
                    )
                    if new_name and new_name not in INVALID_NAMES:
                        resume.candidate_name = new_name
                        db.commit()
                        success_count += 1
                        logger.info(f"  ✅ 成功（从文件名）: {old_name} → {new_name}")
                        continue

                # 优先级3: 从简历正文提取（使用改进的提取逻辑）
                new_name = parser._extract_name(resume.raw_text)
                if new_name and new_name not in INVALID_NAMES:
                    resume.candidate_name = new_name
                    db.commit()
                    success_count += 1
                    logger.info(f"  ✅ 成功（从正文）: {old_name} → {new_name}")
                    continue

                # 所有方法都失败，设为NULL
                resume.candidate_name = None
                db.commit()
                failed_count += 1
                logger.info(f"  ❌ 失败（无法提取有效姓名），设为NULL")

            except Exception as e:
                logger.error(f"  ⚠️  处理失败: {e}")
                db.rollback()
                failed_count += 1

        # 4. 输出统计
        logger.info("\n" + "=" * 80)
        logger.info(f"修复完成！")
        logger.info(f"  成功修复: {success_count} 份")
        logger.info(f"  失败（设为NULL）: {failed_count} 份")
        logger.info(f"  跳过: {skipped_count} 份")
        logger.info(f"  总计: {len(invalid_resumes)} 份")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"错误: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始智能重试提取候选人姓名...\n")
    retry_extract_names()
