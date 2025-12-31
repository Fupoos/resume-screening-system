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

        # 获取未读邮件
        emails = email_service.fetch_unread_emails(
            filter_keywords=None,  # 不过滤关键词，处理所有带附件的邮件
            sender_whitelist=[]  # 发件人白名单
        )

        logger.info(f"找到 {len(emails)} 封符合条件的未读邮件（已过滤：必须有PDF/DOCX附件）")

        # 处理每封邮件
        for idx, email_info in enumerate(emails):
            logger.info(f"准备处理第 {idx+1}/{len(emails)} 封邮件: {email_info['subject'][:50]}... (附件数: {len(email_info['attachments'])})")
            process_email.delay(email_info, email_config)

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
            # 下载附件
            file_path = email_service.download_attachment(
                email_info['id'],
                file_name,
                RESUME_SAVE_PATH
            )

            if file_path:
                logger.info(f"附件已下载: {file_path}")
                # 解析简历
                parse_resume.delay(file_path, email_info)

        # 如果没有附件但有正文，尝试解析正文
        if not has_attachments and email_info.get('body'):
            logger.info(f"尝试解析邮件正文: {email_info['subject'][:50]}...")
            parse_email_body.delay(email_info, email_config)

        # 移动邮件到已处理文件夹
        email_service.move_to_folder(email_info['id'], '已处理')

        # 断开连接
        email_service.disconnect()

    except Exception as e:
        logger.error(f"处理邮件时出错: {e}")


@celery_app.task(name='app.tasks.email_tasks.parse_resume')
def parse_resume(file_path: str, email_info: dict):
    """解析简历并保存到数据库（带去重检查）"""
    from app.core.database import SessionLocal
    from app.models.resume import Resume
    from app.models.screening_result import ScreeningResult
    from app.services.job_matcher import JobMatcher
    from app.api.v1.jobs import preset_jobs
    from app.services.city_extractor import CityExtractor
    from app.services.job_title_classifier import JobTitleClassifier
    from app.services.agent_client import AgentClient
    from app.services.screening_classifier import ScreeningClassifier

    logger.info(f"解析简历: {file_path}")

    db = SessionLocal()
    try:
        # 0. 检查简历是否已存在（通过file_path去重）
        existing_resume = db.query(Resume).filter(Resume.file_path == file_path).first()
        if existing_resume:
            logger.info(f"简历已存在，跳过: {file_path} (ID: {existing_resume.id})")
            return

        # 1. 解析简历
        parser = ResumeParser()
        email_subject = email_info.get('subject')
        email_body = email_info.get('body', '')
        resume_data = parser.parse_resume(file_path, email_subject=email_subject)

        logger.info(f"简历解析完成: {resume_data.get('candidate_name')}")

        # 2. 提取城市（新增）
        city_extractor = CityExtractor()
        city = city_extractor.extract_city(
            email_subject=email_subject,
            email_body=email_body,
            resume_text=resume_data.get('raw_text', '')
        )
        logger.info(f"提取城市: {city or '未知'}")

        # 3. 判断具体职位（新增）
        job_classifier = JobTitleClassifier()
        job_title = job_classifier.classify_job_title(
            email_subject=email_subject,
            resume_text=resume_data.get('raw_text', ''),
            skills=resume_data.get('skills', []),
            skills_by_level=resume_data.get('skills_by_level', {})
        )
        logger.info(f"判断职位: {job_title}")

        # 4. 调用外部Agent（新增）
        agent_client = AgentClient()
        agent_result = agent_client.evaluate_resume(
            job_title=job_title,
            city=city,
            pdf_path=file_path,
            resume_data=resume_data
        )
        logger.info(f"Agent评分: {agent_result['score']}")

        # 5. 分类（新增）
        screening_classifier = ScreeningClassifier()
        screening_status = screening_classifier.classify(agent_result['score'])
        logger.info(f"筛选结果: {screening_status}")

        # 6. 保存简历到数据库（修改）
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
            file_type=file_path.split('.')[-1] if '.' in file_path else None,
            source_email_id=email_info.get('id'),
            source_email_subject=email_info.get('subject'),
            source_sender=email_info.get('sender'),
            # 新增字段
            city=city,
            job_category=job_title,
            pdf_path=file_path,
            agent_score=agent_result['score'],
            agent_evaluation_id=agent_result.get('evaluation_id'),
            agent_evaluated_at=datetime.utcnow(),
            screening_status=screening_status,
            status='processed'
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        logger.info(f"简历已保存到数据库: {resume.id}")

        # 3. 自动匹配所有岗位
        job_matcher = JobMatcher()
        resume_dict = {
            'candidate_name': resume.candidate_name,
            'phone': resume.phone,
            'email': resume.email,
            'education': resume.education,
            'work_years': resume.work_years or 0,
            'skills': resume.skills or []
        }

        top_matches = job_matcher.auto_match_resume(
            resume=resume_dict,
            jobs=preset_jobs,  # preset_jobs已经是字典列表
            top_n=2
        )

        logger.info(f"自动匹配完成，获得 {len(top_matches)} 个匹配结果")

        # 4. 保存匹配结果
        for match in top_matches:
            screening = ScreeningResult(
                resume_id=resume.id,
                job_id=match['job_id'],
                match_score=match['match_score'],
                skill_score=match['skill_score'],
                experience_score=match['experience_score'],
                education_score=match['education_score'],
                matched_points=match['matched_points'],
                unmatched_points=match['unmatched_points'],
                screening_result=match['screening_result'],
                suggestion=match['suggestion']
            )
            db.add(screening)

        db.commit()
        logger.info(f"简历处理完成: {resume.candidate_name}, 保存了 {len(top_matches)} 个匹配结果")

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
    logger.info(f"开始抓取最近 {limit} 封邮件中的简历...")

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

            # 优先扫描包含"已处理"/"processed"/"Processed"的文件夹
            folders_to_scan = []  # List of decoded names
            processed_folder = None

            # 先找"已处理"文件夹
            for fn in folder_names:
                if '已处理' in fn or 'processed' in fn.lower() or 'Processed' in fn:
                    processed_folder = fn
                    folders_to_scan.insert(0, fn)  # 优先处理
                    break

            # 再找INBOX
            for fn in folder_names:
                if 'INBOX' in fn.upper() and fn != processed_folder:
                    folders_to_scan.append(fn)
                    break

            # 如果还没找到，添加其他文件夹
            for fn in folder_names:
                if fn not in folders_to_scan and fn != processed_folder:
                    folders_to_scan.append(fn)
                    if len(folders_to_scan) >= 3:  # 最多扫描3个文件夹
                        break

            logger.info(f"将扫描文件夹: {folders_to_scan}")

        except Exception as e:
            logger.error(f"获取文件夹列表失败: {e}")
            folder_map = {'INBOX': 'INBOX'}  # Fallback mapping
            folders_to_scan = ['INBOX']

        all_emails = []
        total_found = 0

        for folder_decoded in folders_to_scan:
            logger.info(f"扫描文件夹: {folder_decoded}")

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
                filter_keywords=None,
                sender_whitelist=[]
            )

            logger.info(f"文件夹 {folder_decoded} 中找到 {len(emails)} 封符合条件的邮件")
            all_emails.extend(emails)
            total_found += len(emails)

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

        # 处理每封邮件（限制数量）
        processed_count = 0
        for idx, email_info in enumerate(unique_emails[:limit]):
            logger.info(
                f"准备处理第 {idx+1}/{min(len(unique_emails), limit)} 封邮件: "
                f"{email_info['subject'][:50]}... (附件数: {len(email_info['attachments'])})"
            )
            process_email.delay(email_info, email_config)
            processed_count += 1

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
        return result

    except Exception as e:
        logger.error(f"抓取邮件时出错: {e}")
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

        # 只获取未读邮件
        emails = email_service.fetch_unread_emails(
            filter_keywords=None,
            sender_whitelist=[]
        )

        logger.info(f"找到 {len(emails)} 封未读邮件（有PDF/DOCX附件）")

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


@celery_app.task(name='app.tasks.email_tasks.parse_email_body')
def parse_email_body(email_info: dict, email_config: dict):
    """解析邮件正文并提取候选人信息"""
    from app.core.database import SessionLocal
    from app.models.resume import Resume
    from app.models.screening_result import ScreeningResult
    from app.services.job_matcher import JobMatcher
    from app.api.v1.jobs import preset_jobs
    import re

    logger.info(f"解析邮件正文: {email_info['subject']}")

    db = SessionLocal()
    try:
        # 使用邮件ID作为唯一标识（去重）
        unique_id = f"email_{email_info['id']}"
        existing_resume = db.query(Resume).filter(Resume.file_path == unique_id).first()
        if existing_resume:
            logger.info(f"邮件正文已处理过，跳过: {email_info['id']}")
            return

        # 提取正文中的候选人信息
        body = email_info.get('body', '')
        subject = email_info.get('subject', '')

        # 使用正则表达式提取候选人姓名
        candidate_name = None

        # 格式1: BOSS直聘 - "姓名 | X年，应聘 岗位"
        name_match = re.search(r'^([\u4e00-\u9fa5]{2,4})\s*\|', subject)
        if name_match:
            candidate_name = name_match.group(1)
        else:
            # 格式2: 实习僧网 - "岗位-姓名-学校"
            name_match2 = re.search(r'-([\u4e00-\u9fa5]{2,4})-', subject)
            if name_match2:
                candidate_name = name_match2.group(1)
            else:
                # 格式3: 鱼泡直聘 - "姓名|应聘岗位"
                name_match3 = re.search(r'^([\u4e00-\u9fa5]{2,4})\|', subject)
                if name_match3:
                    candidate_name = name_match3.group(1)
                else:
                    # 格式4: 在正文中查找 "姓名 |"
                    name_match4 = re.search(r'([\u4e00-\u9fa5]{2,4})\s*\|', body[:500])
                    if name_match4:
                        # 过滤掉一些常见的关键词
                        name = name_match4.group(1)
                        if name not in ['销售总监', '零售行业', '垂直平台', '财务实施', '市场运营', '销售代表']:
                            candidate_name = name

        # 提取手机号（优先在正文找）
        phone_match = re.search(r'1[3-9]\d{9}', body)
        phone = phone_match.group(0) if phone_match else None

        # 提取邮箱
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', body)
        email_addr = email_match.group(0) if email_match else None

        # 提取工作经验（例如："1年"，"2年以上"，"25年应届生"）
        experience_match = re.search(r'(\d+)\s*年', subject)
        if experience_match:
            work_years = int(experience_match.group(1))
        else:
            experience_match2 = re.search(r'(\d+)\s*年', body)
            work_years = int(experience_match2.group(1)) if experience_match2 else 0

        # 如果是应届生，工作经验设为0
        if '应届' in subject or '应届' in body:
            work_years = 0

        # 提取应聘岗位
        job_match = re.search(r'应聘\s*([^\s|【]+)', subject)
        target_position = job_match.group(1) if job_match else None

        logger.info(f"提取候选人信息: 姓名={candidate_name}, 手机={phone}, 邮箱={email_addr}, 工作经验={work_years}年")

        # 提取技能（使用ResumeParser）
        from app.services.resume_parser import ResumeParser
        parser = ResumeParser()
        email_body_full = body[:10000]  # 使用前10000字符提取技能
        extracted_skills = parser._extract_skills(email_body_full)

        logger.info(f"从邮件正文提取到 {len(extracted_skills)} 个技能: {extracted_skills[:10]}")

        # 提取城市（新增）
        city_extractor = CityExtractor()
        city = city_extractor.extract_city(
            email_subject=subject,
            email_body=body,
            resume_text=body[:5000]
        )
        logger.info(f"提取城市: {city or '未知'}")

        # 判断具体职位（新增）
        job_classifier = JobTitleClassifier()
        job_title = job_classifier.classify_job_title(
            email_subject=subject,
            resume_text=body[:5000],
            skills=extracted_skills,
            skills_by_level={}
        )
        logger.info(f"判断职位: {job_title}")

        # 调用外部Agent（新增）
        # 注意：邮件正文没有PDF文件，所以传递空路径
        resume_data = {
            'candidate_name': candidate_name,
            'phone': phone,
            'email': email_addr,
            'skills': extracted_skills,
            'raw_text': body[:5000]
        }
        agent_client = AgentClient()
        agent_result = agent_client.evaluate_resume(
            job_title=job_title,
            city=city,
            pdf_path='',  # 邮件正文无PDF
            resume_data=resume_data
        )
        logger.info(f"Agent评分: {agent_result['score']}")

        # 分类（新增）
        screening_classifier = ScreeningClassifier()
        screening_status = screening_classifier.classify(agent_result['score'])
        logger.info(f"筛选结果: {screening_status}")

        # 保存到数据库（修改）
        resume = Resume(
            candidate_name=candidate_name or "未知候选人",
            phone=phone,
            email=email_addr,
            education=None,
            education_level=None,
            work_years=work_years,
            skills=extracted_skills,  # 使用提取的技能
            skills_by_level={},
            work_experience=[],
            project_experience=[],
            education_history=[],
            raw_text=body[:5000],  # 保存前5000个字符
            file_path=unique_id,
            file_type='email_body',
            source_email_id=email_info.get('id'),
            source_email_subject=email_info.get('subject'),
            source_sender=email_info.get('sender'),
            # 新增字段
            city=city,
            job_category=job_title,
            pdf_path='',  # 邮件正文无PDF
            agent_score=agent_result['score'],
            agent_evaluation_id=agent_result.get('evaluation_id'),
            agent_evaluated_at=datetime.utcnow(),
            screening_status=screening_status,
            status='processed'
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        logger.info(f"邮件正文已保存到数据库: {resume.id}")

        # 自动匹配所有岗位
        job_matcher = JobMatcher()
        resume_dict = {
            'candidate_name': resume.candidate_name,
            'phone': resume.phone,
            'email': resume.email,
            'education': resume.education,
            'work_years': resume.work_years or 0,
            'skills': []
        }

        top_matches = job_matcher.auto_match_resume(
            resume=resume_dict,
            jobs=preset_jobs,
            top_n=2
        )

        # 保存匹配结果
        for match in top_matches:
            screening = ScreeningResult(
                resume_id=resume.id,
                job_id=match['job_id'],
                match_score=match['match_score'],
                skill_score=match['skill_score'],
                experience_score=match['experience_score'],
                education_score=match['education_score'],
                matched_points=match['matched_points'],
                unmatched_points=match['unmatched_points'],
                screening_result=match['screening_result'],
                suggestion=match['suggestion']
            )
            db.add(screening)

        db.commit()
        logger.info(f"邮件正文处理完成: {resume.candidate_name}, 保存了 {len(top_matches)} 个匹配结果")

    except Exception as e:
        db.rollback()
        logger.error(f"解析邮件正文时出错: {e}")
        raise
    finally:
        db.close()
