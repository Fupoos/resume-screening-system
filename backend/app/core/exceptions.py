"""统一异常处理定义"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(Exception):
    """应用基础异常类

    所有自定义异常的基类
    """
    code: str = "APP_ERROR"
    message: str = "应用程序错误"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    details: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is not None:
            self.message = message
        if details is not None:
            self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源未找到异常 (404)"""
    code = "NOT_FOUND"
    message = "资源未找到"
    status_code = status.HTTP_404_NOT_FOUND


class ValidationException(AppException):
    """数据验证失败异常 (400)"""
    code = "VALIDATION_ERROR"
    message = "数据验证失败"
    status_code = status.HTTP_400_BAD_REQUEST


class UnauthorizedException(AppException):
    """未授权异常 (401)"""
    code = "UNAUTHORIZED"
    message = "未授权访问"
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenException(AppException):
    """禁止访问异常 (403)"""
    code = "FORBIDDEN"
    message = "禁止访问"
    status_code = status.HTTP_403_FORBIDDEN


class ConflictException(AppException):
    """资源冲突异常 (409)"""
    code = "CONFLICT"
    message = "资源冲突"
    status_code = status.HTTP_409_CONFLICT


class BusinessLogicException(AppException):
    """业务逻辑异常"""
    code = "BUSINESS_LOGIC_ERROR"
    message = "业务逻辑错误"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class ExternalServiceException(AppException):
    """外部服务异常 (如 FastGPT API 调用失败)"""
    code = "EXTERNAL_SERVICE_ERROR"
    message = "外部服务调用失败"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
