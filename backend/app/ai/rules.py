"""Cheap local rules used to avoid unnecessary AI work."""
from __future__ import annotations


REMINDER_SIGNAL_WORDS = (
    "deadline", "due", "meeting", "conference", "zoom", "calendar",
    "payment", "invoice", "pay by", "amount due", "please reply",
    "rsvp", "confirm", "respond", "action required", "submit",
    "截止", "到期", "会议", "付款", "发票", "回复", "确认", "提交",
)


def should_extract_reminders(email: dict, category: str | None = None) -> bool:
    """Return whether an email has enough signals to warrant reminder extraction."""
    if category in {"spam", "promotion"}:
        return False
    text = f"{email.get('subject', '')}\n{email.get('body', '')}".lower()
    return any(signal in text for signal in REMINDER_SIGNAL_WORDS) or category in {
        "important", "bill", "school_work", "needs_reply",
    }
