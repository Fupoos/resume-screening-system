"""URL下载服务 - 从远程URL下载简历文件"""
import os
import asyncio
import aiohttp
import zipfile
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple
from urllib.parse import urlparse, unquote
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class URLDownloadService:
    """URL下载服务"""

    # 允许的文件类型
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.zip'}

    # 下载超时（秒）
    DOWNLOAD_TIMEOUT = 30

    # 最大文件大小（100MB）
    MAX_FILE_SIZE = 100 * 1024 * 1024

    def __init__(self, save_dir: str = "/app/resume_files"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def _extract_filename(self, url: str) -> str:
        """从URL提取文件名"""
        path = urlparse(url).path
        filename = os.path.basename(path)
        if not filename or '.' not in filename:
            # 使用默认文件名
            filename = f"resume_{hashlib.md5(url.encode()).hexdigest()[:8]}.pdf"
        return filename

    def _parse_content_disposition(self, content_disposition: str, default: str) -> str:
        """解析Content-Disposition头获取文件名"""
        match = re.search(r'filename\*?=(?:UTF-8\'\')?([^;]+)', content_disposition)
        if match:
            filename = match.group(1).strip('"')
            try:
                filename = unquote(filename)
            except:
                pass
            return filename
        return default

    def _is_allowed_file(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS

    def _get_unique_filepath(self, filename: str, prefix: str = "") -> str:
        """生成唯一文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        name, ext = os.path.splitext(filename)
        if prefix:
            new_filename = f"{prefix}_{timestamp}_{name}{ext}"
        else:
            new_filename = f"{timestamp}_{name}{ext}"
        return os.path.join(self.save_dir, new_filename)

    async def download_file(self, url: str) -> Tuple[bool, str, str]:
        """
        下载单个文件

        返回: (成功状态, 文件路径, 错误信息)
        """
        # 验证URL格式
        try:
            parsed = urlparse(url)
            if not parsed.scheme or parsed.scheme not in ['http', 'https']:
                return False, "", f"无效的URL格式: {url}"
        except Exception as e:
            return False, "", f"URL解析失败: {url}"

        # 从URL获取初始文件名
        filename = self._extract_filename(url)

        try:
            timeout = aiohttp.ClientTimeout(total=self.DOWNLOAD_TIMEOUT)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        return False, "", f"下载失败 (HTTP {response.status}): {url}"

                    # 检查文件大小
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > self.MAX_FILE_SIZE:
                        return False, "", f"文件过大: {url}"

                    # 从Content-Disposition获取更准确的文件名
                    content_disposition = response.headers.get('Content-Disposition')
                    if content_disposition:
                        filename = self._parse_content_disposition(content_disposition, filename)

                    # 检查文件类型
                    if not self._is_allowed_file(filename):
                        return False, "", f"不支持的文件类型: {filename}"

                    # 保存文件
                    file_path = self._get_unique_filepath(filename, prefix="url")

                    content = await response.read()
                    if len(content) > self.MAX_FILE_SIZE:
                        return False, "", f"文件过大: {filename}"

                    with open(file_path, 'wb') as f:
                        f.write(content)

                    logger.info(f"URL下载成功: {url} -> {file_path}")
                    return True, file_path, ""

        except asyncio.TimeoutError:
            return False, "", f"下载超时: {url}"
        except aiohttp.ClientError as e:
            return False, "", f"网络错误: {str(e)}"
        except Exception as e:
            logger.error(f"下载文件异常: {url}, 错误: {e}")
            return False, "", f"下载异常: {str(e)}"

    async def download_urls(self, urls: List[str]) -> Dict:
        """
        批量下载多个URL

        返回: {
            "total": 总数,
            "success": 成功数,
            "failed": 失败数,
            "file_paths": 成功的文件路径列表,
            "errors": 失败信息列表
        }
        """
        results = {
            "total": len(urls),
            "success": 0,
            "failed": 0,
            "file_paths": [],
            "errors": []
        }

        if not urls:
            return results

        # 并发下载（限制并发数）
        semaphore = asyncio.Semaphore(5)  # 最多5个并发

        async def download_with_semaphore(url: str):
            async with semaphore:
                return await self.download_file(url)

        tasks = [download_with_semaphore(url) for url in urls]
        download_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(download_results):
            if isinstance(result, Exception):
                results["failed"] += 1
                results["errors"].append({"url": urls[i], "error": str(result)})
            else:
                success, path, error = result
                if success:
                    results["success"] += 1
                    results["file_paths"].append(path)
                else:
                    results["failed"] += 1
                    results["errors"].append({"url": urls[i], "error": error})

        return results

    async def extract_zip(self, zip_path: str) -> Dict:
        """
        解压ZIP文件

        返回: {
            "total": 文件总数,
            "success": 成功解压数,
            "skipped": 跳过数（不支持的文件类型或目录）,
            "failed": 失败数,
            "file_paths": 成功的文件路径列表,
            "errors": 失败信息列表
        }
        """
        results = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "file_paths": [],
            "errors": []
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 检查ZIP文件是否安全（防止路径遍历攻击）
                for file_info in zip_ref.infolist():
                    results["total"] += 1

                    # 安全检查：防止路径遍历
                    if file_info.filename.startswith('..') or file_info.filename.startswith('/') or file_info.filename.startswith('\\'):
                        results["skipped"] += 1
                        results["errors"].append({
                            "file": file_info.filename,
                            "error": "不安全的文件路径"
                        })
                        continue

                    # 跳过目录
                    if file_info.is_dir():
                        results["skipped"] += 1
                        continue

                    # 检查文件类型
                    if not self._is_allowed_file(file_info.filename):
                        results["skipped"] += 1
                        continue

                    # 检查文件大小
                    if file_info.file_size > self.MAX_FILE_SIZE:
                        results["failed"] += 1
                        results["errors"].append({
                            "file": file_info.filename,
                            "error": "文件过大"
                        })
                        continue

                    try:
                        # 解压文件
                        filename = os.path.basename(file_info.filename)
                        if not filename:  # 处理路径中没有文件名的情况
                            filename = f"zip_file_{results['total']}.pdf"
                        file_path = self._get_unique_filepath(filename, prefix="zip")

                        with zip_ref.open(file_info) as source:
                            with open(file_path, 'wb') as target:
                                target.write(source.read())

                        results["success"] += 1
                        results["file_paths"].append(file_path)
                        logger.info(f"ZIP解压成功: {file_info.filename} -> {file_path}")

                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append({
                            "file": file_info.filename,
                            "error": str(e)
                        })
                        logger.error(f"ZIP解压失败: {file_info.filename}, 错误: {e}")

        except zipfile.BadZipFile:
            results["total"] = 0
            results["failed"] = 1
            results["errors"].append({"file": zip_path, "error": "无效的ZIP文件"})
            logger.error(f"无效的ZIP文件: {zip_path}")
        except Exception as e:
            results["errors"].append({"file": zip_path, "error": str(e)})
            logger.error(f"ZIP解压异常: {zip_path}, 错误: {e}")

        return results
