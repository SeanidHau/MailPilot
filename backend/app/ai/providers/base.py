from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.ai import AIError


class AIProvider(ABC):
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
