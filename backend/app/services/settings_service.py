from __future__ import annotations
import json
import base64
import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Setting

AI_SETTINGS_KEY = "ai_config"
SENSITIVE_KEYS = {"openai_api_key", "anthropic_api_key"}

DEFAULT_AI_CONFIG = {
    "provider": "mock",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "openai_model": "gpt-4o",
    "anthropic_api_key": "",
    "anthropic_base_url": "https://api.anthropic.com",
    "anthropic_model": "claude-sonnet-4-5-20250929",
}


def _derive_key(user_id: int) -> bytes:
    return hashlib.sha256(f"mailpilot-enckey-{user_id}".encode()).digest()


def _xor_encrypt(plain: str, user_id: int) -> str:
    if not plain:
        return plain
    key = _derive_key(user_id)
    plain_bytes = plain.encode()
    encrypted = bytes(p ^ key[i % len(key)] for i, p in enumerate(plain_bytes))
    return base64.urlsafe_b64encode(encrypted).decode()


def _xor_decrypt(encoded: str, user_id: int) -> str:
    if not encoded:
        return encoded
    try:
        key = _derive_key(user_id)
        encrypted = base64.urlsafe_b64decode(encoded.encode())
        return bytes(e ^ key[i % len(key)] for i, e in enumerate(encrypted)).decode()
    except Exception:
        return ""


def _build_key(user_id: Optional[int], key: str) -> str:
    return f"u{user_id}:{key}" if user_id else key


def get_ai_config(db: Session, user_id: Optional[int] = None) -> dict:
    db_key = _build_key(user_id, AI_SETTINGS_KEY)
    row = db.query(Setting).filter(Setting.key == db_key).first()
    if row:
        try:
            stored = json.loads(row.value)
            if user_id:
                for k in SENSITIVE_KEYS:
                    if stored.get(k):
                        stored[k] = _xor_decrypt(stored[k], user_id)
            return {**DEFAULT_AI_CONFIG, **stored}
        except (json.JSONDecodeError, TypeError):
            pass
    return dict(DEFAULT_AI_CONFIG)


def save_ai_config(db: Session, config: dict, user_id: Optional[int] = None) -> dict:
    merged = {**DEFAULT_AI_CONFIG, **config}
    if user_id:
        for k in SENSITIVE_KEYS:
            if merged.get(k):
                merged[k] = _xor_encrypt(merged[k], user_id)
    db_key = _build_key(user_id, AI_SETTINGS_KEY)
    value = json.dumps(merged)

    row = db.query(Setting).filter(Setting.key == db_key).first()
    if row:
        row.value = value
        row.user_id = user_id
    else:
        row = Setting(key=db_key, value=value, user_id=user_id)
        db.add(row)

    db.commit()
    db.refresh(row)
    return config  # return unencrypted for API response
