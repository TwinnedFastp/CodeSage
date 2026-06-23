"""
MinIO / S3 对象存储模块

独立封装所有 S3 兼容存储操作，供 auth_service（头像）和其他模块复用。
配置来源：backend.core.config.settings 中的 S3_* 环境变量。
"""
from backend.minio.client import get_s3_client, is_s3_enabled
from backend.minio.storage import (
    generate_presigned_upload_url,
    build_public_url,
    sanitize_filename,
    upload_bytes,
    delete_object,
)

__all__ = [
    "get_s3_client",
    "is_s3_enabled",
    "generate_presigned_upload_url",
    "build_public_url",
    "sanitize_filename",
    "upload_bytes",
    "delete_object",
]
