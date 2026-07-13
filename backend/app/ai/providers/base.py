from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.ai import AIError


class AIProvider(ABC):
    def process_email(self, email: dict, include_reminders: bool = True) -> tuple[dict, Optional[AIError]]:
        """Process an email in one call when a provider supports it.

        The default implementation preserves compatibility for custom providers
        that only implement the original operation-specific methods.
        """
        category, score, classify_error = self.classify_email(email)
        summary, summarize_error = self.summarize_email(email)
        reminders: list[dict] = []
        reminder_error: Optional[AIError] = None
        if include_reminders and category not in {"spam", "promotion"}:
            reminders, reminder_error = self.extract_reminders(email)
        error = classify_error or summarize_error or reminder_error
        return {
            "category": category,
            "importance_score": score,
            "summary": summary,
            "reminders": reminders,
        }, error

    @abstractmethod
    def classify_email(self, email: dict) -> tuple[str, int, Optional[AIError]]:
        ...

    @abstractmethod
    def summarize_email(self, email: dict) -> tuple[str, Optional[AIError]]:
        ...

    @abstractmethod
    def generate_reply(self, email: dict, tone: str) -> tuple[str, Optional[AIError]]:
        ...

    @abstractmethod
    def extract_reminders(self, email: dict) -> tuple[list[dict], Optional[AIError]]:
        ...
