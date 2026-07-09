from __future__ import annotations

import logging

from openai import OpenAI

from app.ai.providers.base import AIProvider
from app.ai import prompts, parsing, retry
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = OpenAI(
            api_key=api_key or None,
            base_url=base_url,
            timeout=settings.ai_request_timeout,
            max_retries=0,  # we handle retries ourselves
        )

    def _api_call(self, fn, default):
        try:
            return fn()
        except Exception as exc:
            logger.error("OpenAI API call failed after all retries: %s", exc)
            return default

    def classify_email(self, email: dict) -> tuple[str, int]:
        def call():
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_classify_prompt(email)}],
                    temperature=0.3,
                    max_tokens=256,
                ),
                "OpenAI classify",
            )
            text = response.choices[0].message.content or ""
            data = parsing.parse_json_response(text)
            category = str(data.get("category", "normal"))
            score = int(data.get("importance_score", 1))
            score = max(1, min(5, score))
            return (category, score)

        return self._api_call(call, ("normal", 1))

    def summarize_email(self, email: dict) -> str:
        def call():
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_summarize_prompt(email)}],
                    temperature=0.3,
                    max_tokens=300,
                ),
                "OpenAI summarize",
            )
            return (response.choices[0].message.content or "").strip()[:500]

        return self._api_call(call, "Unable to summarize email due to an error.")

    def generate_reply(self, email: dict, tone: str) -> str:
        def call():
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_reply_prompt(email, tone)}],
                    temperature=0.5,
                    max_tokens=500,
                ),
                "OpenAI generate_reply",
            )
            return (response.choices[0].message.content or "").strip()

        return self._api_call(call, "Unable to generate reply due to an error.")

    def extract_reminders(self, email: dict) -> list[dict]:
        def call():
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_extract_reminders_prompt(email)}],
                    temperature=0.3,
                    max_tokens=512,
                ),
                "OpenAI extract_reminders",
            )
            text = response.choices[0].message.content or ""
            data = parsing.parse_json_response(text)
            return data if isinstance(data, list) else []

        return self._api_call(call, [])
