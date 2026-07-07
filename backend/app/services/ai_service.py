from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.core.config import settings

_provider = None


def get_ai_provider():
    global _provider
    if _provider is None:
        name = settings.ai_provider.lower()
        if name == "openai":
            _provider = OpenAIProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
            )
        elif name == "anthropic":
            _provider = AnthropicProvider(
                api_key=settings.anthropic_api_key,
                base_url=settings.anthropic_base_url,
                model=settings.anthropic_model,
            )
        else:
            _provider = MockAIProvider()
    return _provider
