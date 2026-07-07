from __future__ import annotations
import json
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.core.config import settings
from app.db.models import Setting

AI_SETTINGS_KEY = "ai_config"
_provider = None


def _read_ai_config(db: Optional[Session] = None) -> dict:
    """Read AI config from DB, falling back to env vars."""
    config = {
        "provider": settings.ai_provider,
        "openai_api_key": settings.openai_api_key,
        "openai_base_url": settings.openai_base_url,
        "openai_model": settings.openai_model,
        "anthropic_api_key": settings.anthropic_api_key,
        "anthropic_base_url": settings.anthropic_base_url,
        "anthropic_model": settings.anthropic_model,
    }
    if db:
        row = db.query(Setting).filter(Setting.key == AI_SETTINGS_KEY).first()
        if row:
            try:
                stored = json.loads(row.value)
                config.update(stored)
            except (json.JSONDecodeError, TypeError):
                pass
    return config


def get_ai_provider(db: Optional[Session] = None):
    global _provider
    if _provider is None:
        config = _read_ai_config(db)
        name = config.get("provider", "mock").lower()
        if name == "openai":
            _provider = OpenAIProvider(
                api_key=config.get("openai_api_key", ""),
                base_url=config.get("openai_base_url", "https://api.openai.com/v1"),
                model=config.get("openai_model", "gpt-4o"),
            )
        elif name == "anthropic":
            _provider = AnthropicProvider(
                api_key=config.get("anthropic_api_key", ""),
                base_url=config.get("anthropic_base_url", "https://api.anthropic.com"),
                model=config.get("anthropic_model", "claude-sonnet-4-5-20250929"),
            )
        else:
            _provider = MockAIProvider()
    return _provider


def reset_ai_provider():
    global _provider
    _provider = None
