"""批量上传简历API"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Query, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import os
import json
from datetime import datetime

from app.core.database import get_db
from app.models.resume import Resume
from app.tasks.email_tasks import parse_resume
from app.services.url_download_service import URLDownloadService

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "/app/resume_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/batch-upload")
async def batch_upload_resumes(
    files: List[UploadFile] = File(..., description="简历文件列表(PDF/DOCX)"),
    limit: int = Query(1000, description="单次上传文件数量限制")
):
    """批量上传本地简历文件

    Args:
        files: 多个简历文件（PDF或DOCX）
        limit: 单次上传数量限制（默认1000）

    Returns:
        上传结果统计
    """
    # 检查文件数量限制
    if len(files) > limit:
        raise HTTPException(
            status_code=400,
            detail=f"单次最多上传{limit}个文件，当前上传了{len(files)}个"
        )

    results = {
        "total": len(files),
        "success": 0,
        "failed": 0,
        "errors": [],
        "file_names": []
    }

    for file in files:
        try:
            # 检查文件类型
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in ['pdf', 'docx', 'doc']:
                results["failed"] += 1
                results["errors"].append({
                    "file": file.filename,
                    "error": f"不支持的文件类型: {file_ext}"
                })
                continue

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # 触发解析任务
            parse_resume.delay(file_path, {"subject": file.filename, "source": "batch_upload"})

            results["success"] += 1
            results["file_names"].append(file.filename)
            logger.info(f"批量上传文件成功: {file.filename}")

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "file": file.filename,
                "error": str(e)
            })
            logger.error(f"批量上传文件失败: {file.filename}, 错误: {e}")

    return {
        "message": f"批量上传完成: {results['success']}个成功, {results['failed']}个失败",
        "results": results
    }


@router.post("/multi-source-upload")
async def multi_source_upload_resumes(
    files: List[UploadFile] = File(default=[], description="本地简历文件列表"),
    urls: Optional[str] = Body(None, description="URL列表，JSON数组字符串"),
    zip_file: Optional[UploadFile] = File(None, description="ZIP压缩包"),
):
    """多来源混合批量上传简历

    支持三种来源：
    1. 本地文件：直接上传的PDF/DOCX文件
    2. URL导入：输入的URL列表，系统下载后处理
    3. ZIP压缩包：自动解压处理内部文件

    总文件数限制（含解压后）：1500个
    """
    url_service = URLDownloadService(UPLOAD_DIR)
    all_results = {
        "local_files": {"total": 0, "success": 0, "failed": 0, "errors": [], "file_paths": []},
        "urls": {"total": 0, "success": 0, "failed": 0, "errors": [], "file_paths": []},
        "zip": {"total": 0, "success": 0, "skipped": 0, "failed": 0, "errors": [], "file_paths": []},
        "overall": {"total": 0, "success": 0, "failed": 0}
    }
    all_file_paths = []

    # 1. 处理本地文件
    for file in files:
        all_results["local_files"]["total"] += 1
        try:
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in ['pdf', 'docx', 'doc']:
                all_results["local_files"]["failed"] += 1
                all_results["local_files"]["errors"].append({
                    "file": file.filename,
                    "error": f"不支持的文件类型: {file_ext}"
                })
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"local_{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            all_results["local_files"]["success"] += 1
            all_results["local_files"]["file_paths"].append(file_path)
            all_file_paths.append(file_path)

        except Exception as e:
            all_results["local_files"]["failed"] += 1
            all_results["local_files"]["errors"].append({
                "file": file.filename,
                "error": str(e)
            })

    # 2. 处理URL下载
    if urls:
        try:
            url_list = json.loads(urls)
            if not isinstance(url_list, list):
                raise ValueError("urls必须是JSON数组")

            url_results = await url_service.download_urls(url_list)
            all_results["urls"] = url_results
            all_file_paths.extend(url_results.get("file_paths", []))

        except json.JSONDecodeError:
            all_results["urls"]["errors"].append({"error": "URL列表JSON格式错误"})
        except Exception as e:
            all_results["urls"]["errors"].append({"error": str(e)})

    # 3. 处理ZIP文件
    if zip_file:
        try:
            # 保存ZIP文件到临时位置
            temp_zip_path = os.path.join(UPLOAD_DIR, f"temp_{datetime.now().timestamp()}.zip")
            with open(temp_zip_path, "wb") as f:
                content = await zip_file.read()
                f.write(content)

            # 解压
            zip_results = await url_service.extract_zip(temp_zip_path)
            all_results["zip"] = zip_results
            all_file_paths.extend(zip_results.get("file_paths", []))

            # 删除临时ZIP文件
            try:
                os.remove(temp_zip_path)
            except:
                pass

        except Exception as e:
            all_results["zip"]["errors"].append({"error": str(e)})

    # 4. 检查总文件数限制
    total_files = len(all_file_paths)
    if total_files > 1500:
        return {
            "message": f"文件总数超过限制(1500)，实际: {total_files}",
            "results": all_results,
            "overall": {
                "total": total_files,
                "processed": 0,
                "exceeded": True
            }
        }

    # 5. 触发解析任务
    for file_path in all_file_paths:
        try:
            parse_resume.delay(file_path, {"subject": os.path.basename(file_path), "source": "multi_source_upload"})
            all_results["overall"]["success"] += 1
        except Exception as e:
            logger.error(f"触发解析任务失败: {file_path}, 错误: {e}")
            all_results["overall"]["failed"] += 1

    all_results["overall"]["total"] = total_files

    return {
        "message": f"多来源上传完成: 本地文件 {all_results['local_files']['success']}/{all_results['local_files']['total']}, "
                   f"URL下载 {all_results['urls']['success']}/{all_results['urls'].get('total', 0)}, "
                   f"ZIP解压 {all_results['zip']['success']}/{all_results['zip'].get('total', 0)}",
        "results": all_results
    }


@router.get("/upload-status")
async def get_upload_status(db: Session = Depends(get_db)):
    """获取上传统计信息"""
    total = db.query(Resume).count()
    return {
        "total_resumes": total,
        "upload_dir": UPLOAD_DIR
    }
