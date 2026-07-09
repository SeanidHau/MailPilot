from __future__ import annotations

import logging

from anthropic import Anthropic

from app.ai.providers.base import AIProvider
from app.ai import prompts, parsing, retry
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = Anthropic(
            api_key=api_key or None,
            base_url=base_url,
            timeout=settings.ai_request_timeout,
            max_retries=0,  # we handle retries ourselves
        )

    def _api_call(self, fn, default):
        try:
            return fn()
        except Exception as exc:
            logger.error("Anthropic API call failed after all retries: %s", exc)
            return default

    def classify_email(self, email: dict) -> tuple[str, int]:
        def call():
            response = retry.with_retry(
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompts.build_classify_prompt(email)}],
                ),
                "Anthropic classify",
            )
            text = self._extract_text(response)
            data = parsing.parse_json_response(text)
            category = str(data.get("category", "normal"))
            score = int(data.get("importance_score", 1))
            score = max(1, min(5, score))
            return (category, score)

        return self._api_call(call, ("normal", 1))

    def summarize_email(self, email: dict) -> str:
        def call():
            response = retry.with_retry(
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompts.build_summarize_prompt(email)}],
                ),
                "Anthropic summarize",
            )
            return self._extract_text(response).strip()[:500]

        return self._api_call(call, "Unable to summarize email due to an error.")

    def generate_reply(self, email: dict, tone: str) -> str:
        def call():
            response = retry.with_retry(
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompts.build_reply_prompt(email, tone)}],
                ),
                "Anthropic generate_reply",
            )
            return self._extract_text(response).strip()

        return self._api_call(call, "Unable to generate reply due to an error.")

    def extract_reminders(self, email: dict) -> list[dict]:
        def call():
            response = retry.with_retry(
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompts.build_extract_reminders_prompt(email)}],
                ),
                "Anthropic extract_reminders",
            )
            text = self._extract_text(response)
            data = parsing.parse_json_response(text)
            return data if isinstance(data, list) else []

        return self._api_call(call, [])

    @staticmethod
    def _extract_text(response) -> str:
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""
