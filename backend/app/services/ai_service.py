from __future__ import annotations
import json
from threading import Lock
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.core.config import settings

_providers: dict[Optional[int], object] = {}
_provider_lock = Lock()


def get_ai_provider(db: Optional[Session] = None, user_id: Optional[int] = None):
    with _provider_lock:
        provider = _providers.get(user_id)
        if provider is not None:
            return provider

        if user_id and db:
            from app.services.settings_service import get_ai_config
            config = get_ai_config(db, user_id)
        else:
            config = {
                "provider": settings.ai_provider,
                "openai_api_key": settings.openai_api_key,
                "openai_base_url": settings.openai_base_url,
                "openai_model": settings.openai_model,
                "anthropic_api_key": settings.anthropic_api_key,
                "anthropic_base_url": settings.anthropic_base_url,
                "anthropic_model": settings.anthropic_model,
            }

        name = config.get("provider", "mock").lower()
        if name == "openai":
            provider = OpenAIProvider(
                api_key=config.get("openai_api_key", ""),
                base_url=config.get("openai_base_url", "https://api.openai.com/v1"),
                model=config.get("openai_model", "gpt-4o"),
            )
        elif name == "anthropic":
            provider = AnthropicProvider(
                api_key=config.get("anthropic_api_key", ""),
                base_url=config.get("anthropic_base_url", "https://api.anthropic.com"),
                model=config.get("anthropic_model", "claude-sonnet-4-5-20250929"),
            )
        else:
            provider = MockAIProvider()
        _providers[user_id] = provider
        return provider


def reset_ai_provider():
    with _provider_lock:
        _providers.clear()
