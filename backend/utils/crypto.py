"""
字段级加密工具（Fernet 对称加密）

用途：对数据库中的敏感字段（如登录 IP、用户事实记忆中的 PII）进行加密存储，
满足"对用户敏感数据进行加密存储"的安全要求。

设计：
- 密钥来源 settings.FIELD_ENCRYPTION_KEY；为空时生成临时密钥（仅开发）。
- encrypt() 返回字符串（可直接存入 VARCHAR/TEXT），未加密原文不落盘。
- decrypt() 还原原文；对 None/空串原样返回。
- 提供 encrypt/decrypt 的幂等保护：已加密的密文不会被二次加密（前缀标识）。
"""
from __future__ import annotations

import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from backend.core.config import settings

logger = logging.getLogger(__name__)

# 密文标识前缀，便于幂等识别
_CIPHER_PREFIX = "enc::"


def _load_fernet() -> Fernet:
    key = settings.FIELD_ENCRYPTION_KEY.strip()
    if not key:
        # 开发模式：生成临时密钥并告警
        tmp = Fernet.generate_key()
        logger.warning(
            "FIELD_ENCRYPTION_KEY 未配置，使用临时内存密钥，重启后将无法解密历史加密数据！"
            "生产环境请通过环境变量配置。"
        )
        return Fernet(tmp)
    return Fernet(key.encode())


# 模块级单例（首次访问时初始化）
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _load_fernet()
    return _fernet


def encrypt(plaintext: Optional[str]) -> Optional[str]:
    """加密明文。None / 空串原样返回；已是密文则原样返回（幂等）。"""
    if plaintext is None or plaintext == "":
        return plaintext
    if isinstance(plaintext, str) and plaintext.startswith(_CIPHER_PREFIX):
        return plaintext
    token = _get_fernet().encrypt(plaintext.encode("utf-8"))
    return _CIPHER_PREFIX + token.decode("ascii")


def decrypt(ciphertext: Optional[str]) -> Optional[str]:
    """解密密文。None/空串/非密文原样返回，保证读取历史未加密数据兼容。"""
    if ciphertext is None or ciphertext == "":
        return ciphertext
    if not (isinstance(ciphertext, str) and ciphertext.startswith(_CIPHER_PREFIX)):
        # 兼容历史未加密数据
        return ciphertext
    token = ciphertext[len(_CIPHER_PREFIX):].encode("ascii")
    try:
        return _get_fernet().decrypt(token).decode("utf-8")
    except InvalidToken:
        logger.error("字段解密失败：密钥不匹配或密文损坏")
        return None
