"""Symmetric encryption for sensitive stored data using Fernet (AES-128-CBC + HMAC)."""
from __future__ import annotations

import logging

from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    if key:
        try:
            return Fernet(key.encode())
        except Exception:
            logger.warning("Invalid ENCRYPTION_KEY in config, generating a temporary one.")
    key = Fernet.generate_key().decode()
    logger.warning(
        "No valid ENCRYPTION_KEY set. A temporary key has been generated for this session. "
        "Set ENCRYPTION_KEY in .env for production."
    )
    return Fernet(key.encode())


def _ensure_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _get_fernet()
    return _fernet


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    return _ensure_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    if not token:
        return token
    try:
        return _ensure_fernet().decrypt(token.encode()).decode()
    except Exception:
        logger.warning("Failed to decrypt stored value, returning empty string.")
        return ""
