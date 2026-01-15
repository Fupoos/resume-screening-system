"""文件访问API - 支持PDF预览和DOCX转HTML"""
import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, Response, HTMLResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.models.resume import Resume

router = APIRouter()
logger = logging.getLogger(__name__)

# 文件存储目录
PDF_DIR = "/app/resume_files"


def get_file_media_type(file_path: str) -> str:
    """根据文件扩展名获取MIME类型"""
    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
    }
    return media_types.get(ext, 'application/octet-stream')


@router.get("/{resume_id}/preview", response_class=HTMLResponse)
def get_resume_preview(resume_id: UUID, db: Session = Depends(get_db)):
    """获取简历预览HTML（DOCX转HTML）

    Args:
        resume_id: 简历ID

    Returns:
        HTML格式的简历内容
    """
    # 查询简历
    resume = db.query(Resume).filter(Resume.id == resume_id).first()

    if not resume:
        logger.error(f"简历不存在: resume_id={resume_id}")
        raise HTTPException(status_code=404, detail="简历不存在")

    # 获取文件路径
    file_path = resume.pdf_path or resume.file_path

    if not file_path:
        logger.error(f"简历没有文件路径: resume_id={resume_id}, candidate={resume.candidate_name}")
        raise HTTPException(status_code=404, detail="简历没有关联的文件")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(
            f"文件不存在: path={file_path}, "
            f"resume_id={resume_id}, candidate={resume.candidate_name}"
        )
        raise HTTPException(status_code=404, detail=f"文件不存在: {os.path.basename(file_path)}")

    # 获取文件扩展名
    ext = os.path.splitext(file_path)[1].lower()

    # PDF文件直接返回提示（使用另一个端点）
    if ext == '.pdf':
        return HTMLResponse(
            content='<div style="padding:20px;text-align:center;">请使用PDF预览端点</div>',
            status_code=200
        )

    # DOCX/DOC文件转换为HTML
    if ext in ['.docx', '.doc']:
        try:
            import mammoth
            # 直接传入文件对象
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(
                    docx_file,
                    style_map="p[style-name='Title'] => h1:fresh\np[style-name='Heading 1'] => h2:fresh\np[style-name='Heading 2'] => h3:fresh"
                )
                html_content = result.value
            # 添加样式
            styled_html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; padding: 20px; }}
                    h1 {{ font-size: 20px; font-weight: bold; margin: 16px 0 8px 0; }}
                    h2 {{ font-size: 18px; font-weight: bold; margin: 14px 0 6px 0; }}
                    h3 {{ font-size: 16px; font-weight: bold; margin: 12px 0 4px 0; }}
                    p {{ margin: 6px 0; }}
                    ul, ol {{ margin: 8px 0; padding-left: 24px; }}
                    li {{ margin: 4px 0; }}
                    table {{ border-collapse: collapse; margin: 12px 0; }}
                    td, th {{ border: 1px solid #ddd; padding: 6px 10px; }}
                    strong {{ font-weight: bold; }}
                </style>
            </head>
            <body>{html_content}</body>
            </html>
            """
            return HTMLResponse(content=styled_html)
        except ImportError:
            logger.error("mammoth库未安装")
            raise HTTPException(status_code=500, detail="服务器缺少DOCX预览所需的库")
        except Exception as e:
            logger.error(f"转换DOCX失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"转换DOCX失败: {str(e)}")

    raise HTTPException(status_code=400, detail="不支持的文件类型")


@router.get("/{resume_id}")
def get_resume_file(resume_id: UUID, db: Session = Depends(get_db)):
    """获取简历PDF文件

    Args:
        resume_id: 简历ID

    Returns:
        PDF文件
    """
    # 查询简历
    resume = db.query(Resume).filter(Resume.id == resume_id).first()

    if not resume:
        logger.error(f"简历不存在: resume_id={resume_id}")
        raise HTTPException(status_code=404, detail="简历不存在")

    # 只返回PDF文件
    file_path = resume.pdf_path or resume.file_path

    if not file_path:
        logger.error(f"简历没有文件路径: resume_id={resume_id}, candidate={resume.candidate_name}")
        raise HTTPException(
            status_code=404,
            detail="简历没有关联的文件"
        )

    # 检查文件扩展名，只处理PDF
    ext = os.path.splitext(file_path)[1].lower()
    if ext != '.pdf':
        # 对于非PDF文件，返回错误或重定向到preview端点
        raise HTTPException(
            status_code=400,
            detail="此端点仅支持PDF预览，请使用/preview端点查看DOCX"
        )

    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(
            f"文件不存在: path={file_path}, "
            f"resume_id={resume_id}, candidate={resume.candidate_name}"
        )
        raise HTTPException(
            status_code=404,
            detail=f"文件不存在: {os.path.basename(file_path)}"
        )

    filename = os.path.basename(file_path)

    # 对文件名进行URL编码
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=filename,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        }
    )
