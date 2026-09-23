"""密码单向哈希（不可逆）；库中只存 hash，看不到明文。"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_PBKDF2_ROUNDS = 120_000


def hash_password(password: str) -> str:
    """生成带盐 PBKDF2-SHA256 摘要，格式 ``salt$digest``。"""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ROUNDS,
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """校验密码。兼容旧版无盐 SHA256（64 位 hex）。"""
    if "$" not in stored:
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored)

    salt, expected = stored.split("$", 1)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ROUNDS,
    ).hex()
    return hmac.compare_digest(digest, expected)
