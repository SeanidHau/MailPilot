from app.ai.providers.mock import MockAIProvider
from app.core.config import settings

_provider = None


def get_ai_provider():
    global _provider
    if _provider is None:
        if settings.ai_provider == "mock":
            _provider = MockAIProvider()
        else:
            _provider = MockAIProvider()
    return _provider
