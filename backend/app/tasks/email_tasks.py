"""邮箱任务 - Celery异步任务"""
import os
from datetime import datetime
from pathlib import Path
from celery import shared_task
from app.tasks.celery_app import celery_app
from app.services.email_service import EmailService
from app.services.resume_parser import ResumeParser
import logging

logger = logging.getLogger(__name__)

# 简历文件保存路径
RESUME_SAVE_PATH = os.getenv('RESUME_SAVE_PATH', '/app/resume_files')


@celery_app.task(name='app.tasks.email_tasks.check_emails')
def check_emails():
    """检查新邮件并处理简历附件"""
    logger.info("开始检查邮箱...")

    # TODO: 从数据库获取邮箱配置
    # 目前使用硬编码的配置（后续改为从数据库读取）
    email_config = {
        'email_address': os.getenv('DEMO_EMAIL', 'es1@cloudpense.com'),
        'auth_code': os.getenv('DEMO_AUTH_CODE', ''),
        'imap_server': 'imap.exmail.qq.com',
        'imap_port': 993,
        'folder': 'INBOX'
    }

    if not email_config['auth_code']:
        logger.warning("未配置邮箱授权码，跳过邮件检查")
        return

    # 创建邮箱服务
    email_service = EmailService(
        email_address=email_config['email_address'],
        auth_code=email_config['auth_code'],
        imap_server=email_config['imap_server'],
        imap_port=email_config['imap_port'],
        folder=email_config['folder']
    )

    try:
        # 连接邮箱
        if not email_service.connect():
            logger.error("连接邮箱失败")
            return

        # 获取未读邮件（不再过滤）
        emails = email_service.fetch_unread_emails(
            save_path=RESUME_SAVE_PATH  # 直接保存附件
        )


        logger.info(f"找到 {len(emails)} 封未读邮件")

        # 处理每封邮件
        for idx, email_info in enumerate(emails):
            logger.info(f"准备处理第 {idx+1}/{len(emails)} 封邮件: {email_info['subject'][:50]}... (附件数: {len(email_info['attachments'])})")
            celery_app.send_task('app.tasks.email_tasks.process_email', args=[email_info, email_config])

        # 断开连接
        email_service.disconnect()

    except Exception as e:
        logger.error(f"检查邮箱时出错: {e}")


@celery_app.task(name='app.tasks.email_tasks.process_email')
def process_email(email_info: dict, email_config: dict):
    """处理单封邮件"""
    logger.info(f"处理邮件: {email_info['subject']}")

    email_service = EmailService(
        email_address=email_config['email_address'],
        auth_code=email_config['auth_code'],
        imap_server=email_config['imap_server'],
        imap_port=email_config['imap_port']
    )

    if not email_service.connect():
        logger.error("连接邮箱失败")
        return

    try:
        # 检查是否有附件
        has_attachments = False
        for attachment in email_info['attachments']:
            file_name = attachment['filename']

            # 只处理简历文件
            if not file_name.endswith(('.pdf', '.PDF', '.docx', '.DOCX', '.doc', '.DOC')):
                continue

            has_attachments = True

            # 优先使用已保存的路径（在fetch时已保存）
            file_path = attachment.get('saved_path')

            # 如果没有保存路径，尝试重新下载
            if not file_path:
                file_path = email_service.download_attachment(
                    email_info['id'],
                    file_name,
                    RESUME_SAVE_PATH
                )

            if file_path:
                logger.info(f"使用附件文件: {file_path}")
                # 解析简历（使用send_task确保任务被正确发送）
                celery_app.send_task('app.tasks.email_tasks.parse_resume', args=[file_path, email_info])
                logger.info(f"已触发解析任务: {file_path}")

        # 没有PDF附件的邮件跳过处理（符合CLAUDE.md原则2：只保留有PDF+正文的简历）
        if not has_attachments:
            logger.info(f"邮件无PDF附件，跳过处理: {email_info['subject'][:50]}...")

        # 断开连接
        email_service.disconnect()

        # 更新进度（邮件处理完成，无论是否有附件）
        # 注意：这里统一计数，parse_resume中不再计数，避免重复
        try:
            from app.api.v1.email_monitoring import increment_import_success
            increment_import_success()
        except Exception as status_err:
            logger.warning(f"更新状态失败: {status_err}")

    except Exception as e:
        logger.error(f"处理邮件时出错: {e}")


@celery_app.task(name='app.tasks.email_tasks.parse_resume')
def parse_resume(file_path: str, email_info: dict):
    """解析简历并保存到数据库（带去重检查）

    多阶段Agent处理流程：
    1. Agent1 (FastGPT) 解析简历 + 提取信息 + 职位分类
    2. 路由到外部评分 Agent 进行评分
    3. 本地系统根据分数进行筛选分类

    降级策略：
    - 如果 Agent1 失败，降级到本地解析（但跳过评分）
    """
    from app.core.database import SessionLocal
    from app.models.resume import Resume
    from app.services.city_extractor import CityExtractor
    from app.services.agents.resume_orchestrator import ResumeOrchestrator

    logger.info(f"解析简历: {file_path}")

    db = SessionLocal()
    try:
        email_subject = email_info.get('subject')
        email_body = email_info.get('body', '')

        # 1. 首先获取简历文本（使用本地解析器提取文本）
        parser = ResumeParser()
        resume_data = parser.parse_resume(file_path, email_subject=email_subject)

        # 🔴 新增：处理无正文内容的简历（保存为需要人工审核）
        needs_manual_review = False
        if not resume_data.get('raw_text'):
            logger.warning(f"简历无正文内容��将标记为需要人工审核: {file_path}")
            needs_manual_review = True
            # 尝试从文件名或邮件主题提取候选人姓名
            candidate_name = resume_data.get('candidate_name')
            if not candidate_name:
                # 从文件名提取姓名
                import os
                import re
                filename = os.path.basename(file_path)
                # 尝试从文件名中提取中文姓名
                name_match = re.search(r'([\u4e00-\u9fa5]{2,4})', filename)
                if name_match:
                    candidate_name = name_match.group(1)
                else:
                    candidate_name = "待补充��名"

            # 设置默认值
            resume_data['raw_text'] = ""  # 空字符串表示无正文
            resume_data['skills'] = []
            resume_data['education'] = None
            resume_data['work_years'] = 0
            resume_data['phone'] = None
            resume_data['email'] = None

        logger.info(f"简历解析完成: {resume_data.get('candidate_name')}")

        # 2. 使用多阶段 Agent 编排器处理
        if needs_manual_review:
            # 无正文内容，跳过 Agent 处理，标记为需要人工审核
            orchestrator_result = {
                "success": True,
                "parsed_info": resume_data,
                "job_category": None,
                "agent_score": None,
                "screening_status": "needs_review",
                "evaluation_id": None,
                "processing_details": {"fallback_used": False}
            }
            logger.info(f"简历无正文，跳过 Agent 处理，标记为需要人工审核")
            job_category = None
            agent_score = None
            screening_status = "needs_review"
            evaluation_id = None
            city = None
            candidate_cities = []
            merged_resume_data = resume_data
        else:
            # 提取城市（统一处理，后续可用）
            city_extractor = CityExtractor()
            city_result = city_extractor.extract_city(
                email_subject=email_subject,
                email_body=email_body,
                resume_text=resume_data.get('raw_text', '')
            )
            city = city_result.confirmed_city
            candidate_cities = city_result.candidate_cities
            logger.info(f"提取城市 - 确认: {city or '无'}, 候选: {candidate_cities or '无'}")

            # 有正文内容，使用编排器进行多阶段处理
            logger.info("使用 ResumeOrchestrator 进行多阶段 Agent 处理")
            orchestrator = ResumeOrchestrator(db)
            orchestrator_result = orchestrator.process_resume_with_fallback(
                resume_text=resume_data.get('raw_text', ''),
                pdf_path=file_path
            )

            if not orchestrator_result.get("success"):
                logger.error(f"Orchestrator 处理失败: {orchestrator_result.get('error')}")
                # 即使失败也尝试保存基本信息
                orchestrator_result = {
                    "success": True,
                    "parsed_info": resume_data,
                    "job_category": None,
                    "agent_score": None,
                    "screening_status": "pending",
                    "evaluation_id": None,
                    "processing_details": {"fallback_used": True}
                }

            # 3. 从处理结果中提取数据
            parsed_info = orchestrator_result.get("parsed_info", {})
            job_category = orchestrator_result.get("job_category")
            agent_score = orchestrator_result.get("agent_score")
            screening_status = orchestrator_result.get("screening_status", "pending")
            evaluation_id = orchestrator_result.get("evaluation_id")

            # 合并解析结果（优先使用 orchestrator 的结果）
            merged_resume_data = {**resume_data, **parsed_info}

            logger.info(f"处理结果 - 职位: {job_category}, 评分: {agent_score}, 状态: {screening_status}")
            city = city_result.confirmed_city
            candidate_cities = city_result.candidate_cities

        # 设置评估时间
        from datetime import datetime
        agent_evaluated_at = datetime.utcnow() if agent_score is not None else None

        # 4. 检查简历是否已存在（基于姓名+手机号去重）
        candidate_name = resume_data.get('candidate_name')
        phone = resume_data.get('phone')

        existing_resume = None
        if candidate_name and phone:
            # 优先使用姓名+手机号去重
            existing_resume = db.query(Resume).filter(
                Resume.candidate_name == candidate_name,
                Resume.phone == phone
            ).first()
        elif candidate_name:
            # 如果没有手机号，仅使用姓名去重
            existing_resume = db.query(Resume).filter(
                Resume.candidate_name == candidate_name
            ).first()

        # merged_resume_data 在两个分支中都已定义，直接使用
        final_resume_data = merged_resume_data

        if existing_resume:
            # 更新现有简历记录
            logger.info(f"简历已存在（姓名: {candidate_name}, 手机: {phone}），更新记录: {existing_resume.id}")
            existing_resume.phone = final_resume_data.get('phone') or existing_resume.phone
            existing_resume.email = final_resume_data.get('email') or existing_resume.email
            existing_resume.education = final_resume_data.get('education')
            existing_resume.education_level = final_resume_data.get('education_level')
            existing_resume.work_years = final_resume_data.get('work_years', 0)
            existing_resume.skills = final_resume_data.get('skills', [])
            existing_resume.skills_by_level = final_resume_data.get('skills_by_level', {})
            existing_resume.work_experience = final_resume_data.get('work_experience', [])
            existing_resume.project_experience = final_resume_data.get('project_experience', [])
            existing_resume.education_history = final_resume_data.get('education_history', [])
            existing_resume.raw_text = final_resume_data.get('raw_text')
            existing_resume.file_path = file_path  # 更新为最新文件路径
            existing_resume.file_type = file_path.split('.')[-1] if '.' in file_path else None
            existing_resume.source_email_id = email_info.get('id')
            existing_resume.source_email_subject = email_info.get('subject')
            existing_resume.source_sender = email_info.get('sender')
            existing_resume.city = city
            existing_resume.candidate_cities = candidate_cities
            existing_resume.job_category = job_category
            existing_resume.pdf_path = file_path
            existing_resume.agent_score = agent_score
            existing_resume.agent_evaluation_id = evaluation_id
            existing_resume.agent_evaluated_at = agent_evaluated_at
            existing_resume.screening_status = screening_status
            existing_resume.status = 'processed'

            db.commit()
            db.refresh(existing_resume)
            resume = existing_resume
        else:
            # 创建新简历记录
            resume = Resume(
                candidate_name=final_resume_data.get('candidate_name'),
                phone=final_resume_data.get('phone'),
                email=final_resume_data.get('email'),
                education=final_resume_data.get('education'),
                education_level=final_resume_data.get('education_level'),
                work_years=final_resume_data.get('work_years', 0),
                skills=final_resume_data.get('skills', []),
                skills_by_level=final_resume_data.get('skills_by_level', {}),
                work_experience=final_resume_data.get('work_experience', []),
                project_experience=final_resume_data.get('project_experience', []),
                education_history=final_resume_data.get('education_history', []),
                raw_text=final_resume_data.get('raw_text'),
                file_path=file_path,
                file_type=file_path.split('.')[-1] if '.' in file_path else None,
                source_email_id=email_info.get('id'),
                source_email_subject=email_info.get('subject'),
                source_sender=email_info.get('sender'),
                city=city,
                candidate_cities=candidate_cities,
                job_category=job_category,
                pdf_path=file_path,
                agent_score=agent_score,
                agent_evaluation_id=evaluation_id,
                agent_evaluated_at=agent_evaluated_at,
                screening_status=screening_status,
                status='processed'
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

        if needs_manual_review:
            logger.info(f"简历已保存到数据库（需人工审核）: {resume.id}")
        else:
            logger.info(f"简历已保存到数据库: {resume.id}")

        # ❌ 已删除本地JobMatcher自动匹配（违反核心原则）

        # 输出处理完成日志
        if needs_manual_review:
            logger.info(f"简历处理完成（需人工审核）: {resume.candidate_name}, 无正文内容")
        elif agent_score is not None:
            logger.info(f"简历处理完成: {resume.candidate_name}, Agent评分: {agent_score}")
        else:
            logger.info(f"简历处理完成: {resume.candidate_name}, 职位: {job_category}")

        # 不再更新进度，因为process_email已经计数了

    except Exception as e:
        db.rollback()
        logger.error(f"处理简历时出错: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name='app.tasks.email_tasks.fetch_recent_resumes')
def fetch_recent_resumes(limit: int = 20):
    """抓取最近N封邮件中的简历附件（从近到远，扫描所有文件夹）

    Args:
        limit: 抓取邮件数量（默认20封）
    """
    from app.api.v1.email_monitoring import update_import_status

    logger.info(f"开始抓取最近 {limit} 封邮件中的简历...")

    # 更新状态：开始扫描
    update_import_status(
        running=True,
        total=0,
        processed=0,
        current_folder="正在连接邮箱...",
        message="正在扫描邮箱文件夹"
    )

    email_config = {
        'email_address': os.getenv('DEMO_EMAIL', 'es1@cloudpense.com'),
        'auth_code': os.getenv('DEMO_AUTH_CODE', ''),
        'imap_server': 'imap.exmail.qq.com',
        'imap_port': 993,
        'folder': 'INBOX'
    }

    if not email_config['auth_code']:
        logger.warning("未配置邮箱授权码，跳过")
        return {'status': 'error', 'message': '未配置邮箱授权码'}

    # 创建邮箱服务
    email_service = EmailService(
        email_address=email_config['email_address'],
        auth_code=email_config['auth_code'],
        imap_server=email_config['imap_server'],
        imap_port=email_config['imap_port'],
        folder=email_config['folder']
    )

    try:
        # 连接邮箱
        if not email_service.connect():
            logger.error("连接邮箱失败")
            return {'status': 'error', 'message': '连接邮箱失败'}

        # 获取所有文件夹列表
        try:
            status, folders = email_service.client.list()
            logger.info(f"IMAP list() status: {status}, 返回数据类型: {type(folders)}, 数量: {len(folders) if folders else 0}")

            # 导入 IMAP UTF-7 解码器
            from imapclient.imap_utf7 import decode

            # 存储文件夹信息：{decoded_name: encoded_name}
            folder_map = {}
            for line in folders:
                # line 格式: b'(\\HasNoChildren) "/" "folder_name"'
                if isinstance(line, bytes):
                    line_str = line.decode('latin-1')
                else:
                    line_str = str(line)

                # 提取文件夹名（在最后一个引号中）
                import re
                match = re.search(r'"([^"]+)"\s*$', line_str)
                if match:
                    folder_encoded = match.group(1)
                    # 解码 IMAP UTF-7 (使用 imapclient 的 decode 函数，需要 bytes 输入)
                    try:
                        folder_name_decoded = decode(folder_encoded.encode('latin-1'))
                    except:
                        folder_name_decoded = folder_encoded
                    logger.info(f"解析文件夹: {folder_encoded} -> {folder_name_decoded}")

                    # 存储映射：decoded -> encoded
                    folder_map[folder_name_decoded] = folder_encoded

            # 获取所有已解码的文件夹名列表
            folder_names = list(folder_map.keys())
            logger.info(f"找到文件夹: {folder_names}")

            # 扫描文件夹的顺序：INBOX优先，然后是其他文件夹
            folders_to_scan = []  # List of decoded names

            # 先找INBOX
            for fn in folder_names:
                if 'INBOX' in fn.upper():
                    folders_to_scan.append(fn)
                    break

            # 添加所有其他文件夹（不再限制3个）
            for fn in folder_names:
                if fn not in folders_to_scan:
                    # 排除一些不需要的文件夹
                    if fn not in ['Drafts', 'Sent Messages', 'Deleted Messages', 'Junk']:
                        folders_to_scan.append(fn)

            logger.info(f"将扫描文件夹: {folders_to_scan}")

            # 更新状态：找到文件夹
            update_import_status(
                current_folder=f"找到 {len(folders_to_scan)} 个文件夹",
                message=f"将扫描: {', '.join(folders_to_scan[:3])}{'...' if len(folders_to_scan) > 3 else ''}"
            )

        except Exception as e:
            logger.error(f"获取文件夹列表失败: {e}")
            update_import_status(message=f"获取文件夹列表失败: {e}")
            folder_map = {'INBOX': 'INBOX'}  # Fallback mapping
            folders_to_scan = ['INBOX']

        all_emails = []
        total_found = 0

        for folder_decoded in folders_to_scan:
            logger.info(f"扫描文件夹: {folder_decoded}")

            # 更新状��：正在扫描文件夹
            update_import_status(
                current_folder=f"正在扫描: {folder_decoded}",
                message=f"扫描文件夹 {len(folders_to_scan)}/{folders_to_scan.index(folder_decoded) + 1}"
            )

            # 获取编码后的文件夹名（用于 IMAP 操作）
            folder_encoded = folder_map.get(folder_decoded, folder_decoded)

            # 切换到目标文件夹
            try:
                # 使用 IMAP UTF-7 编码的文件夹名
                email_service.client.select(folder_encoded)
            except Exception as e:
                # 如果失败，尝试引用的方式
                try:
                    email_service.client.select('"{}"'.format(folder_encoded))
                except Exception as e2:
                    logger.warning(f"无法切换到文件夹 {folder_decoded} (encoded: {folder_encoded}): {e2}")
                    continue

            # 获取该文件夹的邮件
            fetch_limit = limit if limit < 1000 else 9999  # 如果limit>=1000，表示获取全部
            emails = email_service.fetch_recent_emails(
                limit=fetch_limit,
                save_path=RESUME_SAVE_PATH  # 直接保存附件
            )

            logger.info(f"文件夹 {folder_decoded} 中找到 {len(emails)} 封邮件")
            all_emails.extend(emails)
            total_found += len(emails)

            # 更新状态：找到邮件
            update_import_status(
                total=total_found,
                message=f"在 {folder_decoded} 中找到 {len(emails)} 封邮件"
            )

            # 如果已经找到足够的邮件且不是获取全部模式，停止扫描
            if fetch_limit < 1000 and len(all_emails) >= fetch_limit:
                logger.info(f"已找到 {len(all_emails)} 封邮件，达到目标数量")
                break

        # 去重：通过邮件ID
        seen_ids = set()
        unique_emails = []
        for email in all_emails:
            if email['id'] not in seen_ids:
                seen_ids.add(email['id'])
                unique_emails.append(email)

        logger.info(f"总共找到 {len(unique_emails)} 封唯一邮件（去重后）")

        # 更新状态：开始处理邮件
        update_import_status(
            total=len(unique_emails),
            processed=0,
            current_folder="开始处理邮件",
            message=f"找到 {len(unique_emails)} 封待处理邮件"
        )

        # 处理每封邮件（限制数量）
        processed_count = 0
        for idx, email_info in enumerate(unique_emails[:limit]):
            logger.info(
                f"准备处理第 {idx+1}/{min(len(unique_emails), limit)} 封邮件: "
                f"{email_info['subject'][:50]}... (附件数: {len(email_info['attachments'])})"
            )
            process_email.delay(email_info, email_config)
            processed_count += 1

            # 每10封邮件更新一次状态
            if (idx + 1) % 10 == 0 or idx == len(unique_emails[:limit]) - 1:
                update_import_status(
                    processed=idx + 1,
                    message=f"已处理 {idx + 1}/{len(unique_emails)} 封邮件"
                )

        # 断开连接
        email_service.disconnect()

        result = {
            'status': 'success',
            'message': f'从 {len(folders_to_scan)} 个文件夹中找到 {total_found} 封邮件，处理了 {processed_count} 封',
            'folders_scanned': folders_to_scan,
            'total_emails_found': total_found,
            'processed': processed_count
        }

        logger.info(f"抓取完成: {result}")

        # 更新状态：扫描完成，等待后台解析
        # 注意：running保持为True，直到所有解析任务完成
        # 这里的message改为"扫描完成"，让前端知道扫描阶段已结束
        update_import_status(
            total=len(unique_emails),
            processed=processed_count,
            current_folder="正在解析简历...",
            message=f"扫描完成，{processed_count}封邮件正在后台解析中..."
        )

        return result

    except Exception as e:
        logger.error(f"抓取邮件时出错: {e}")
        update_import_status(
            running=False,
            current_folder="导入失败",
            message=f"抓取失败: {str(e)}"
        )
        return {'status': 'error', 'message': f'抓取失败: {str(e)}'}


@celery_app.task(name='app.tasks.email_tasks.check_new_emails')
def check_new_emails():
    """检查新的未读邮件（用于定时自动抓取）"""
    logger.info("开始检查新邮件...")

    email_config = {
        'email_address': os.getenv('DEMO_EMAIL', 'es1@cloudpense.com'),
        'auth_code': os.getenv('DEMO_AUTH_CODE', ''),
        'imap_server': 'imap.exmail.qq.com',
        'imap_port': 993,
        'folder': 'INBOX'
    }

    if not email_config['auth_code']:
        logger.warning("未配置邮箱授权码，跳过")
        return {'status': 'error', 'message': '未配置邮箱授权码'}

    # 创建邮箱服务
    email_service = EmailService(
        email_address=email_config['email_address'],
        auth_code=email_config['auth_code'],
        imap_server=email_config['imap_server'],
        imap_port=email_config['imap_port'],
        folder=email_config['folder']
    )

    try:
        # 连接邮箱
        if not email_service.connect():
            logger.error("连接邮箱失败")
            return {'status': 'error', 'message': '连接邮箱失败'}

        # 只获取未读邮件（不再过滤）
        emails = email_service.fetch_unread_emails(
            save_path=RESUME_SAVE_PATH  # 直接保存附件
        )

        logger.info(f"找到 {len(emails)} 封未读邮件")

        if len(emails) == 0:
            logger.info("没有新的未读邮件需要处理")
            email_service.disconnect()
            return {
                'status': 'success',
                'message': '没有新邮件',
                'total_emails': 0,
                'processed': 0
            }

        # 处理每封邮件
        for idx, email_info in enumerate(emails):
            logger.info(
                f"准备处理第 {idx+1}/{len(emails)} 封新邮件: "
                f"{email_info['subject'][:50]}... (附件数: {len(email_info['attachments'])})"
            )
            process_email.delay(email_info, email_config)

        # 断开连接
        email_service.disconnect()

        result = {
            'status': 'success',
            'message': f'成功处理 {len(emails)} 封新邮件',
            'total_emails': len(emails),
            'processed': len(emails)
        }

        logger.info(f"检查完成: {result}")
        return result

    except Exception as e:
        logger.error(f"检查新邮件时出错: {e}")
        return {'status': 'error', 'message': f'检查失败: {str(e)}'}
