"""认证相关API路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    require_admin,
)
from app.models.user import User, UserJobCategory

router = APIRouter()


# ==================== Schema定义 ====================

class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user_info: "UserInfo"


class UserInfo(BaseModel):
    """用户信息"""
    id: UUID
    username: str
    role: str
    job_categories: List[str]
    is_active: bool


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    password: str
    role: str = "user"  # admin / user
    job_categories: List[str] = []  # 岗位类别名称列表，如 ["Java开发", "实施顾问"]


class UserUpdate(BaseModel):
    """更新用户请求"""
    password: Optional[str] = None
    role: Optional[str] = None
    job_categories: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: UUID
    username: str
    role: str
    job_categories: List[str]
    is_active: bool
    created_at: str


# 更新前向引用
TokenResponse.model_rebuild()

# ==================== API端点 ====================

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录（OAuth2 表单格式）"""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    # 获取用户的岗位类别
    job_categories = [ujc.job_category_name for ujc in user.job_categories]

    return TokenResponse(
        access_token=access_token,
        user_info=UserInfo(
            id=user.id,
            username=user.username,
            role=user.role,
            job_categories=job_categories,
            is_active=user.is_active
        )
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    job_categories = [ujc.job_category_name for ujc in current_user.job_categories]
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        job_categories=job_categories,
        is_active=current_user.is_active
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表（仅管理员）"""
    users = db.query(User).all()
    result = []
    for user in users:
        job_categories = [ujc.job_category_name for ujc in user.job_categories]
        result.append(UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            job_categories=job_categories,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None
        ))
    return result


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建用户（仅管理员）"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 创建用户
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True
    )
    db.add(new_user)
    db.flush()  # 获取user.id

    # 分配岗位类别
    for category_name in user_data.job_categories:
        ujc = UserJobCategory(
            user_id=new_user.id,
            job_category_name=category_name
        )
        db.add(ujc)

    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        job_categories=user_data.job_categories,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat()
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新密码
    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)

    # 更新角色
    if user_data.role is not None:
        user.role = user_data.role

    # 更新状态
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    # 更新岗位类别
    if user_data.job_categories is not None:
        # 删除旧的关联
        db.query(UserJobCategory).filter(UserJobCategory.user_id == user_id).delete()
        # 添加新的关联
        for category_name in user_data.job_categories:
            ujc = UserJobCategory(user_id=user_id, job_category_name=category_name)
            db.add(ujc)

    db.commit()
    db.refresh(user)

    job_categories = [ujc.job_category_name for ujc in user.job_categories]
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        job_categories=job_categories,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    db.delete(user)
    db.commit()

    return {"message": "用户已删除"}


@router.get("/job-categories", response_model=List[str])
async def get_available_job_categories(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取系统中可用的岗位类别列表（从简历表中获取）"""
    from app.models.resume import Resume

    # 从简历表中获取所有唯一的job_category
    categories = db.query(Resume.job_category).distinct().filter(
        Resume.job_category.isnot(None),
        Resume.job_category != ''
    ).all()

    return [cat[0] for cat in categories if cat[0]]
