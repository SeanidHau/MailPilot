from __future__ import annotations
import json
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Setting

AI_SETTINGS_KEY = "ai_config"
DEFAULT_AI_CONFIG = {
    "provider": "mock",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "openai_model": "gpt-4o",
    "anthropic_api_key": "",
    "anthropic_base_url": "https://api.anthropic.com",
    "anthropic_model": "claude-sonnet-4-5-20250929",
}


def get_ai_config(db: Session) -> dict:
    row = db.query(Setting).filter(Setting.key == AI_SETTINGS_KEY).first()
    if row:
        try:
            stored = json.loads(row.value)
            return {**DEFAULT_AI_CONFIG, **stored}
        except (json.JSONDecodeError, TypeError):
            pass
    return dict(DEFAULT_AI_CONFIG)


def save_ai_config(db: Session, config: dict) -> dict:
    merged = {**DEFAULT_AI_CONFIG, **config}
    value = json.dumps(merged)

    row = db.query(Setting).filter(Setting.key == AI_SETTINGS_KEY).first()
    if row:
        row.value = value
    else:
        row = Setting(key=AI_SETTINGS_KEY, value=value)
        db.add(row)

    db.commit()
    db.refresh(row)
    return merged
