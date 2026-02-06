"""阿里云OSS文件上传服务"""
import os
import logging
from datetime import datetime
from typing import Optional
import oss2

logger = logging.getLogger(__name__)


class OSSService:
    """阿里云OSS文件上传服务"""

    def __init__(self):
        """初始化OSS客户端"""
        self.access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
        self.access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
        self.bucket_name = os.getenv("OSS_BUCKET", "hross.cloudpense.com")
        self.endpoint = os.getenv("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com")
        self.region = os.getenv("OSS_REGION", "cn-shanghai")

        self.auth = None
        self.bucket = None
        self._init_client()

    def _init_client(self):
        """初始化OSS客户端"""
        if not all([self.access_key_id, self.access_key_secret]):
            logger.warning("OSS配置不完整，上传功能将不可用")
            return

        try:
            self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)

            # 判断是否使用自定义域名
            is_custom_domain = '.' in self.bucket_name and self.bucket_name.endswith('.com')

            if is_custom_domain:
                # 自定义域名：需要指定实际bucket名称用于签名计算
                # 从环境变量获取实际bucket名称
                self.actual_bucket_name = os.getenv("OSS_ACTUAL_BUCKET", "cloudpense-hr")
                endpoint = f"https://{self.bucket_name}"
                self.bucket = oss2.Bucket(self.auth, endpoint, self.actual_bucket_name, is_cname=True)
                logger.info(f"OSS客户端初始化成功(自定义域名): endpoint={endpoint}, bucket={self.actual_bucket_name}")
            else:
                # 标准OSS域名
                endpoint = f"https://{self.endpoint}"
                self.actual_bucket_name = self.bucket_name
                self.bucket = oss2.Bucket(self.auth, endpoint, self.bucket_name)
                logger.info(f"OSS客户端初始化成功(标准): {self.bucket_name}, endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"OSS客户端初始化失败: {e}")

    def is_available(self) -> bool:
        """检查OSS服务是否可用"""
        return self.bucket is not None

    def upload_file(
        self,
        file_path: str,
        object_key: Optional[str] = None,
        folder: str = "resumes",
        use_presigned_url: bool = True
    ) -> Optional[str]:
        """上传文件到OSS

        Args:
            file_path: 本地文件路径
            object_key: OSS对象键，不指定则自动生成
            folder: 存储文件夹
            use_presigned_url: 是否返回签名URL（默认True，有效期2小时）

        Returns:
            OSS文件URL（签名URL或普通URL），失败返回None
        """
        if not self.is_available():
            logger.error("OSS服务不可用")
            return None

        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None

        try:
            # 生成对象键
            if object_key is None:
                filename = os.path.basename(file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                object_key = f"{folder}/{timestamp}_{filename}"

            # 上传文件
            with open(file_path, 'rb') as file:
                result = self.bucket.put_object(object_key, file)

            if result.status == 200:
                # 根据参数返回签名URL或普通URL
                if use_presigned_url:
                    url = self.generate_presigned_url(object_key)
                else:
                    # 构造公开访问URL（自定义域名使用 bucket_name 直接作为域名）
                    if '.' in self.bucket_name and self.bucket_name.endswith('.com'):
                        url = f"https://{self.bucket_name}/{object_key}"
                    else:
                        url = f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
                logger.info(f"文件上传成功: {url}")
                return url
            else:
                logger.error(f"文件上传失败: status={result.status}")
                return None

        except Exception as e:
            logger.error(f"文件上传异常: {e}")
            return None

    def upload_bytes(
        self,
        content: bytes,
        filename: str,
        folder: str = "resumes"
    ) -> Optional[str]:
        """上传字节内容到OSS

        Args:
            content: 文件内容
            filename: 文件名
            folder: 存储文件夹

        Returns:
            OSS文件URL，失败返回None
        """
        if not self.is_available():
            logger.error("OSS服务不可用")
            return None

        try:
            # 生成对象键
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_key = f"{folder}/{timestamp}_{filename}"

            # 上传内容
            result = self.bucket.put_object(object_key, content)

            if result.status == 200:
                # 自定义域名使用 bucket_name 直接作为域名
                if '.' in self.bucket_name and self.bucket_name.endswith('.com'):
                    url = f"https://{self.bucket_name}/{object_key}"
                else:
                    url = f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
                logger.info(f"内容上传成功: {url}")
                return url
            else:
                logger.error(f"内容上传失败: status={result.status}")
                return None

        except Exception as e:
            logger.error(f"内容上传异常: {e}")
            return None

    def generate_presigned_url(
        self,
        object_key: str,
        expires: int = 7200
    ) -> Optional[str]:
        """生成带签名的临时访问URL

        Args:
            object_key: OSS对象键
            expires: 有效期（秒），默认7200秒（2小时）

        Returns:
            带签名的URL，失败返回None
        """
        if not self.is_available():
            logger.error("OSS服务不可用")
            return None

        try:
            # 生成签名URL
            url = self.bucket.sign_url('GET', object_key, expires)
            logger.info(f"生成签名URL成功: {object_key}, 有效期{expires}秒")
            return url
        except Exception as e:
            logger.error(f"生成签名URL失败: {e}")
            return None

    def delete_file(self, object_key: str) -> bool:
        """删除OSS文件

        Args:
            object_key: OSS对象键

        Returns:
            是否删除成功
        """
        if not self.is_available():
            logger.error("OSS服务不可用")
            return False

        try:
            result = self.bucket.delete_object(object_key)
            if result.status == 204:
                logger.info(f"文件删除成功: {object_key}")
                return True
            else:
                logger.error(f"文件删除失败: status={result.status}")
                return False
        except Exception as e:
            logger.error(f"文件删除异常: {e}")
            return False


# 全局单例
_oss_service: Optional[OSSService] = None


def get_oss_service() -> OSSService:
    """获取OSS服务单例"""
    global _oss_service
    if _oss_service is None:
        _oss_service = OSSService()
    return _oss_service
