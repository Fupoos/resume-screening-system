"""FastAPI应用主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智能简历初筛系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "简历智能初筛系统API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 注册路由
from app.api.v1 import jobs, screening, resumes, diagnostics, data_cleanup, statistics, pdfs, upload, auth

# 认证路由（不需要认证即可访问）
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])

# 业务路由（需要认证）
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["岗位"])
app.include_router(screening.router, prefix="/api/v1/screening", tags=["筛选"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["简历"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["批量上传"])
app.include_router(pdfs.router, prefix="/api/v1/pdfs", tags=["PDF查看"])
app.include_router(diagnostics.router, prefix="/api/v1/diagnostics", tags=["诊断"])
app.include_router(data_cleanup.router, prefix="/api/v1/data-cleanup", tags=["数据清理"])
app.include_router(statistics.router, prefix="/api/v1/statistics", tags=["统计"])
