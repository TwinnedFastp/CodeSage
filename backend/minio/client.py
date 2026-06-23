"""
S3 客户端工厂

懒创建 boto3 S3 client，所有配置从 settings.S3_* 读取。
单例缓存避免重复创建连接池。
"""
from __future__ import annotations

import logging
from functools import lru_cache

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from backend.core.config import settings

logger = logging.getLogger(__name__)

# 模块级单例，首次调用时创建，后续复用
_client = None


def is_s3_enabled() -> bool:
    """检查 S3/MinIO 是否已启用且配置完整。"""
    return bool(
        settings.S3_ENABLED
        and settings.S3_ENDPOINT_URL
        and settings.S3_ACCESS_KEY_ID
        and settings.S3_SECRET_ACCESS_KEY
    )


def get_s3_client():
    """
    获取 S3 客户端单例。

    未启用时抛 RuntimeError，调用方应先调 is_s3_enabled() 检查。
    """
    global _client
    if _client is not None:
        return _client

    if not is_s3_enabled():
        raise RuntimeError("S3/MinIO 存储未启用，请检查 S3_ENABLED 和相关配置")

    _client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        use_ssl=settings.S3_USE_SSL,
        config=BotoConfig(signature_version="s3v4"),
    )
    logger.info("S3 客户端已创建 endpoint=%s", settings.S3_ENDPOINT_URL)
    return _client
