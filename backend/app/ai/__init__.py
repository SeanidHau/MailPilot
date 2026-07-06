from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def classify_email(self, email: dict) -> tuple[str, int]:
        ...

    @abstractmethod
    def summarize_email(self, email: dict) -> str:
        ...

    @abstractmethod
    def generate_reply(self, email: dict, tone: str) -> str:
        ...

    @abstractmethod
    def extract_reminders(self, email: dict) -> list[dict]:
        ...
