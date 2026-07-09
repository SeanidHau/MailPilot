import re
from datetime import datetime, timedelta
from typing import Optional

from app.ai.providers.base import AIProvider
from app.schemas.ai import AIError


class MockAIProvider(AIProvider):
    def classify_email(self, email: dict) -> tuple[str, int, Optional[AIError]]:
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()
        text = f"{subject} {body}"

        if any(w in text for w in ["urgent", "deadline", "final notice", "action required", "critical"]):
            return ("important", min(5, self._score_importance(text) + 2), None)

        if any(w in text for w in ["lottery", "winner", "prize", "click here", "free money", "congratulations"]):
            return ("spam", 1, None)

        if any(w in text for w in ["invoice", "receipt", "payment", "due amount", "subscription", "billing"]):
            return ("bill", 3, None)

        if any(w in text for w in ["assignment", "class", "project", "report", "professor", "manager"]):
            return ("school_work", 3, None)

        if any(w in text for w in ["reply", "respond", "confirm", "approve", "feedback", "question"]):
            return ("needs_reply", 3, None)

        if any(w in text for w in ["discount", "sale", "offer", "unsubscribe", "campaign", "promo"]):
            return ("promotion", 2, None)

        return ("normal", self._score_importance(text), None)

    def _score_importance(self, text: str) -> int:
        score = 1
        if any(w in text for w in ["urgent", "asap", "immediately"]):
            score += 2
        if any(w in text for w in ["deadline", "due", "meeting"]):
            score += 1
        if any(w in text for w in ["please", "thank you", "appreciate"]):
            score += 1
        return min(5, max(1, score))

    def summarize_email(self, email: dict) -> tuple[str, Optional[AIError]]:
        body = email.get("body", "")
        sentences = re.split(r"(?<=[.!?])\s+", body.strip())
        if len(sentences) <= 2:
            return body[:500] if body else "No content to summarize.", None

        first = sentences[0] if sentences else ""
        key_points = [s for s in sentences[1:4] if len(s) > 20]
        if not key_points:
            return first[:500], None

        summary = f"{first}\n\nKey points:\n"
        for i, pt in enumerate(key_points, 1):
            summary += f"- {pt.strip()[:200]}\n"
        return summary[:500], None

    def generate_reply(self, email: dict, tone: str) -> tuple[str, Optional[AIError]]:
        sender = email.get("sender", "there")
        subject = email.get("subject", "your email")

        templates = {
            "formal": f"Dear {sender},\n\nThank you for your email regarding \"{subject}\". I have reviewed the details and will respond with a complete reply shortly.\n\nShould you have any additional questions, please do not hesitate to reach out.\n\nBest regards,\n[MailPilot User]",
            "brief": f"Hi {sender},\n\nGot it, thanks. I'll follow up soon.\n\nBest",
            "polite_decline": f"Dear {sender},\n\nThank you for your message about \"{subject}\". After careful review, I regret to inform you that I am unable to proceed at this time. I appreciate your understanding.\n\nBest regards,\n[MailPilot User]",
            "ask_info": f"Hi {sender},\n\nThanks for your email regarding \"{subject}\". To help me move forward, could you please provide the following:\n\n- Additional details about the matter\n- Any relevant timelines or deadlines\n- Supporting documents if available\n\nLooking forward to your response.\n\nBest,\n[MailPilot User]",
        }
        return templates.get(tone, templates["formal"]), None

    def extract_reminders(self, email: dict) -> tuple[list[dict], Optional[AIError]]:
        subject = email.get("subject", "")
        body = email.get("body", "")
        text = f"{subject}\n{body}"
        reminders = []

        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}/\d{2}/\d{4})",
            r"(\w+ \d{1,2},?\s*\d{4})",
            r"by (\w+) (\d{1,2})(?:st|nd|rd|th)?",
        ]

        due_at = None
        for pat in date_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    due_at = m.group(0)
                except Exception:
                    pass
                break

        if any(w in text.lower() for w in ["deadline", "due by", "due date"]):
            reminders.append({
                "title": f"Deadline: {subject[:80]}",
                "description": "Deadline mentioned in email",
                "reminder_type": "deadline",
                "due_at": due_at,
            })

        if any(w in text.lower() for w in ["meeting", "conference call", "zoom", "calendar"]):
            reminders.append({
                "title": f"Meeting: {subject[:80]}",
                "description": "Meeting scheduled in email",
                "reminder_type": "meeting",
                "due_at": due_at,
            })

        if any(w in text.lower() for w in ["payment", "invoice", "pay by", "amount due"]):
            reminders.append({
                "title": f"Payment: {subject[:80]}",
                "description": "Payment notice in email",
                "reminder_type": "payment",
                "due_at": due_at,
            })

        if any(w in text.lower() for w in ["please reply", "rsvp", "confirm", "respond by"]):
            reminders.append({
                "title": f"Reply needed: {subject[:80]}",
                "description": "This email needs a response",
                "reminder_type": "reply_task",
                "due_at": due_at,
            })

        if not reminders:
            reminders.append({
                "title": f"Follow up: {subject[:80]}",
                "description": "Consider following up on this email",
                "reminder_type": "other",
                "due_at": (datetime.now() + timedelta(days=2)).isoformat(),
            })

        return reminders, None
