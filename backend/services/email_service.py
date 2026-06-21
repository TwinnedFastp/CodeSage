"""
邮箱服务

- 生产模式：SMTP_HOST 配置后使用 aiosmtplib 异步发送
- 开发模式：SMTP_HOST 为空时，把验证链接打印到日志并返回，便于本地联调

验证链接格式：{VERIFY_EMAIL_BASE_URL}/verify-email?token=xxx
"""
from __future__ import annotations

import logging
from typing import Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.core.config import settings

logger = logging.getLogger(__name__)


def build_verify_link(token: str) -> str:
    """构造邮箱验证链接。"""
    base = settings.VERIFY_EMAIL_BASE_URL.rstrip("/")
    return f"{base}/verify-email?token={token}"


async def send_verification_email(to_email: str, token: str) -> Optional[str]:
    """
    发送邮箱验证邮件。

    返回值：
    - 开发模式：返回验证链接（调用方可在响应中带出，方便联调）
    - 生产模式：None（链接已通过 SMTP 发出，不回传）
    """
    link = build_verify_link(token)
    subject = "【CodeSage】请验证您的邮箱（24 小时内有效）"
    body = (
        f"欢迎注册 CodeSage！\n\n"
        f"请在 24 小时内点击下方链接完成邮箱验证：\n{link}\n\n"
        f"若非本人操作，请忽略此邮件。\n"
    )

    if not settings.SMTP_HOST:
        # 开发模式：打印到日志，并回传链接便于测试
        logger.warning("SMTP 未配置，验证邮件内容打印到日志（开发模式）")
        logger.info("==== 验证邮件 ====\n收件人: %s\n主题: %s\n%s\n==================", to_email, subject, body)
        return link

    # 生产模式：SMTP 发送
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_PORT == 587,
            use_tls=settings.SMTP_PORT == 465,
        )
        logger.info("验证邮件已发送至 %s", to_email)
        return None
    except Exception:
        logger.exception("发送验证邮件失败（收件人: %s）", to_email)
        raise RuntimeError("验证邮件发送失败，请稍后重试或联系管理员")
