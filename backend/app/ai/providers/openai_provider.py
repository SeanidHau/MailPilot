from __future__ import annotations

import logging
from typing import Optional

from openai import OpenAI

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


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = OpenAI(
            api_key=api_key or None,
            base_url=base_url,
            timeout=settings.ai_request_timeout,
            max_retries=0,
        )

    def process_email(self, email: dict, include_reminders: bool = True) -> tuple[dict, Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_process_prompt(email, include_reminders)}],
                    temperature=0.2,
                    max_tokens=700,
                ),
                "OpenAI process_email",
            )
            data = parsing.parse_process_response(response.choices[0].message.content or "")
            if not include_reminders:
                data["reminders"] = []
            return data, None
        except Exception as exc:
            logger.error("OpenAI process_email failed: %s", exc)
            return {
                "category": "normal",
                "importance_score": 1,
                "summary": "暂时无法生成摘要，请稍后重试。",
                "reminders": [],
            }, _classify_error(exc)

    def classify_email(self, email: dict) -> tuple[str, int, Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_classify_prompt(email)}],
                    temperature=0.3, max_tokens=256,
                ),
                "OpenAI classify",
            )
            text = response.choices[0].message.content or ""
            data = parsing.parse_json_response(text)
            category = str(data.get("category", "normal"))
            score = max(1, min(5, int(data.get("importance_score", 1))))
            return category, score, None
        except Exception as exc:
            logger.error("OpenAI classify failed: %s", exc)
            return "normal", 1, _classify_error(exc)

    def summarize_email(self, email: dict) -> tuple[str, Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_summarize_prompt(email)}],
                    temperature=0.3, max_tokens=300,
                ),
                "OpenAI summarize",
            )
            return (response.choices[0].message.content or "").strip()[:500], None
        except Exception as exc:
            logger.error("OpenAI summarize failed: %s", exc)
            return "暂时无法生成摘要，请稍后重试。", _classify_error(exc)

    def generate_reply(self, email: dict, tone: str) -> tuple[str, Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_reply_prompt(email, tone)}],
                    temperature=0.5, max_tokens=500,
                ),
                "OpenAI generate_reply",
            )
            return (response.choices[0].message.content or "").strip(), None
        except Exception as exc:
            logger.error("OpenAI generate_reply failed: %s", exc)
            return "Unable to generate reply due to an error.", _classify_error(exc)

    def extract_reminders(self, email: dict) -> tuple[list[dict], Optional[AIError]]:
        try:
            response = retry.with_retry(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompts.build_extract_reminders_prompt(email)}],
                    temperature=0.3, max_tokens=512,
                ),
                "OpenAI extract_reminders",
            )
            text = response.choices[0].message.content or ""
            data = parsing.parse_json_response(text)
            return (data if isinstance(data, list) else []), None
        except Exception as exc:
            logger.error("OpenAI extract_reminders failed: %s", exc)
            return [], _classify_error(exc)
