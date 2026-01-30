"""认证与授权核心模块"""
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import bcrypt  # 直接使用 bcrypt，避免 passlib 初始化问题

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserJobCategory

# HTTP Bearer token 认证
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 直接使用 bcrypt 避免 passlib 初始化问题"""
    # bcrypt 有72字节限制，截断密码
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    # 截断到72字节
    plain_password = plain_password[:72]
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希 - 直接使用 bcrypt"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    # 截断到72字节
    password = password[:72]
    # 生成 salt 并哈希
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


class PermissionChecker:
    """权限检查器"""

    @staticmethod
    def is_admin(user: User) -> bool:
        """检查用户是否为管理员"""
        return user.role == "admin"

    @staticmethod
    def get_user_job_categories(user: User) -> List[str]:
        """获取用户可访问的岗位类别列表"""
        if user.role == "admin":
            return []  # 空列表表示无限制

        categories = [ujc.job_category_name for ujc in user.job_categories]
        return categories


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限的依赖"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def get_accessible_job_categories(current_user: User = Depends(get_current_user)) -> Optional[List[str]]:
    """获取用户可访问的岗位类别（用于数据过滤）"""
    if current_user.role == "admin":
        return None  # None 表示无限制
    return [ujc.job_category_name for ujc in current_user.job_categories]
