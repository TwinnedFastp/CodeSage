"""
对象存储操作封装

提供预签名 URL 生成、文件上传、删除等通用操作。
所有方法均异步友好（boto3 同步调用通过 asyncio.to_thread 包装）。
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from botocore.exceptions import ClientError

from backend.core.config import settings
from backend.minio.client import get_s3_client, is_s3_enabled

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    清理文件名：去除路径分隔符，只保留字母数字点下划线连字符。
    空文件名返回 'file'。
    """
    name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-_")
    return name or "file"


def build_public_url(object_key: str, bucket: Optional[str] = None) -> str:
    """
    构建对象的公开访问 URL。

    如果配置了 S3_PUBLIC_BASE_URL，用它拼接；否则返回 object_key 本身
    （适用于 MinIO 直接通过 endpoint 访问的场景）。
    """
    bucket = bucket or settings.S3_BUCKET_AVATARS
    base = settings.S3_PUBLIC_BASE_URL.rstrip("/")
    if base:
        return f"{base}/{bucket}/{object_key}"
    return object_key


async def generate_presigned_upload_url(
    object_key: str,
    content_type: str,
    bucket: Optional[str] = None,
    expires_in: Optional[int] = None,
) -> dict:
    """
    生成预签名上传 URL（PUT 方法）。

    返回：
    {
        "upload_url": str,   # 预签名 PUT URL（已用 public_base 替换 endpoint）
        "object_key": str,   # 对象存储 key
        "public_url": str,   # 上传后的公开访问 URL
        "expires_in": int,   # 有效期秒数
    }

    异常：S3 未启用或生成失败时抛 RuntimeError。
    """
    if not is_s3_enabled():
        raise RuntimeError("S3/MinIO 存储未启用")

    bucket = bucket or settings.S3_BUCKET_AVATARS
    expires_in = expires_in or settings.S3_PRESIGN_EXPIRE_SECONDS
    client = get_s3_client()

    try:
        upload_url = await asyncio.to_thread(
            client.generate_presigned_url,
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
    except ClientError as exc:
        logger.exception("生成预签名上传 URL 失败 key=%s", object_key)
        raise RuntimeError(f"生成上传 URL 失败：{exc}") from exc

    # 如果配置了 public_base，用 public_base 替换 endpoint，让前端访问的是公开域名
    public_base = settings.S3_PUBLIC_BASE_URL.rstrip("/")
    if public_base and settings.S3_ENDPOINT_URL:
        upload_url = upload_url.replace(settings.S3_ENDPOINT_URL.rstrip("/"), public_base)

    return {
        "upload_url": upload_url,
        "object_key": object_key,
        "public_url": build_public_url(object_key, bucket),
        "expires_in": expires_in,
    }


async def upload_bytes(
    data: bytes,
    object_key: str,
    content_type: str = "application/octet-stream",
    bucket: Optional[str] = None,
) -> str:
    """
    直接上传字节数据到 S3（服务端直接上传，不走预签名）。

    返回公开访问 URL。适用于服务端生成的文件（如导出 PDF）。
    """
    if not is_s3_enabled():
        raise RuntimeError("S3/MinIO 存储未启用")

    bucket = bucket or settings.S3_BUCKET_AVATARS
    client = get_s3_client()

    try:
        await asyncio.to_thread(
            client.put_object,
            Bucket=bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )
    except ClientError as exc:
        logger.exception("上传文件失败 key=%s", object_key)
        raise RuntimeError(f"上传文件失败：{exc}") from exc

    return build_public_url(object_key, bucket)


async def delete_object(
    object_key: str,
    bucket: Optional[str] = None,
) -> bool:
    """删除 S3 对象，成功返回 True，对象不存在也返回 True。"""
    if not is_s3_enabled():
        return False

    bucket = bucket or settings.S3_BUCKET_AVATARS
    client = get_s3_client()

    try:
        await asyncio.to_thread(
            client.delete_object,
            Bucket=bucket,
            Key=object_key,
        )
        return True
    except ClientError as exc:
        logger.exception("删除对象失败 key=%s", object_key)
        return False
