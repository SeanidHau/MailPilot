from __future__ import annotations

import logging
from typing import Optional

from anthropic import Anthropic

from app.ai.providers.base import AIProvider
from app.ai import prompts, parsing, retry
from app.core.config import settings
from app.schemas.ai import AIError

logger = logging.getLogger(__name__)


def _classify_error(exc: Exception) -> AIError:
    msg = str(exc)
    status = getattr(exc, "status_code", None)
    if status == 401 or status == 403:
        return AIError(message=msg, type="auth_error", retryable=False)
    if status == 429:
        return AIError(message=msg, type="rate_limit", retryable=True)
    if status and status >= 500:
        return AIError(message=msg, type="server_error", retryable=True)
    if "timeout" in msg.lower():
        return AIError(message=msg, type="timeout", retryable=True)
    return AIError(message=msg, type="provider_error", retryable=False)


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = Anthropic(
            api_key=api_key or None,
            base_url=base_url,
            timeout=settings.ai_request_timeout,
            max_retries=0,
        )

    def process_email(self, email: dict, include_reminders: bool = True) -> tuple[dict, Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=700,
                    messages=[{"role": "user", "content": prompts.build_process_prompt(email, include_reminders)}],
                ),
                "Anthropic process_email",
            )
            data = parsing.parse_process_response(self._extract_text(response))
            if not include_reminders:
                data["reminders"] = []
            return data, None
        except Exception as exc:
            logger.error("Anthropic process_email failed: %s", exc)
            return {
                "category": "normal",
                "importance_score": 1,
                "summary": "暂时无法生成摘要，请稍后重试。",
                "reminders": [],
            }, _classify_error(exc)

    def classify_email(self, email: dict) -> tuple[str, int, Optional[AIError]]:
        try:
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
            score = max(1, min(5, int(data.get("importance_score", 1))))
            return category, score, None
        except Exception as exc:
            logger.error("Anthropic classify failed: %s", exc)
            return "normal", 1, _classify_error(exc)

    def summarize_email(self, email: dict) -> tuple[str, Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompts.build_summarize_prompt(email)}],
                ),
                "Anthropic summarize",
            )
            return self._extract_text(response).strip()[:500], None
        except Exception as exc:
            logger.error("Anthropic summarize failed: %s", exc)
            return "暂时无法生成摘要，请稍后重试。", _classify_error(exc)

    def generate_reply(self, email: dict, tone: str) -> tuple[str, Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompts.build_reply_prompt(email, tone)}],
                ),
                "Anthropic generate_reply",
            )
            return self._extract_text(response).strip(), None
        except Exception as exc:
            logger.error("Anthropic generate_reply failed: %s", exc)
            return "Unable to generate reply due to an error.", _classify_error(exc)

    def extract_reminders(self, email: dict) -> tuple[list[dict], Optional[AIError]]:
        try:
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
            return (data if isinstance(data, list) else []), None
        except Exception as exc:
            logger.error("Anthropic extract_reminders failed: %s", exc)
            return [], _classify_error(exc)

    @staticmethod
    def _extract_text(response) -> str:
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""
