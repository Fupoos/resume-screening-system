"""PDF文件访问API"""
import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.resume import Resume

router = APIRouter()
logger = logging.getLogger(__name__)

# PDF文件存储目录
PDF_DIR = "/app/resume_files"


@router.get("/{resume_id}")
def get_resume_pdf(resume_id: UUID, db: Session = Depends(get_db)):
    """获取简历PDF文件
    
    Args:
        resume_id: 简历ID
        
    Returns:
        PDF文件
    """
    # 查询简历
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    
    # 检查是否有文件路径
    if not resume.file_path:
        raise HTTPException(status_code=404, detail="简历没有关联的PDF文件")
    
    # 检查文件是否存在
    if not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail=f"PDF文件不存在: {resume.file_path}")
    
    # 返回PDF文件
    filename = os.path.basename(resume.file_path)
    
    return FileResponse(
        path=resume.file_path,
        media_type='application/pdf',
        filename=filename,
        headers={
            "Content-Disposition": f"inline; filename=\"{filename}\""
        }
    )
