MAX_BODY_LENGTH = 3000

CATEGORIES = [
    ("important", "urgent, deadlines, critical issues"),
    ("normal", "general correspondence"),
    ("promotion", "marketing, discounts, campaigns, sales"),
    ("bill", "invoices, payments, subscriptions"),
    ("school_work", "academic or work tasks, assignments"),
    ("needs_reply", "requires response or confirmation"),
    ("spam", "suspicious, unwanted, or fraudulent"),
]

TONES = {
    "formal": "Complete, professional, and polite",
    "brief": "Short, direct, and concise",
    "polite_decline": "Respectful refusal",
    "ask_info": "Request clarification or additional details",
}

REMINDER_TYPES = "deadline, meeting, payment, reply_task, other"


def _fmt_email(email: dict) -> str:
    subject = email.get("subject", "")
    sender = email.get("sender", "")
    body = (email.get("body", "") or "")[:MAX_BODY_LENGTH]
    return f"Subject: {subject}\nSender: {sender}\nBody: {body}"


def build_classify_prompt(email: dict) -> str:
    cat_desc = "\n".join(f"- {c}: {d}" for c, d in CATEGORIES)
    email_text = _fmt_email(email)
    return (
        "You are an email classifier. Analyze the email below and respond ONLY with a JSON object "
        "containing exactly two fields:\n"
        "- category: one of the following categories\n"
        "- importance_score: an integer from 1 (lowest) to 5 (highest)\n\n"
        f"Categories:\n{cat_desc}\n\n"
        "Example response: {\"category\": \"important\", \"importance_score\": 5}\n\n"
        "Rules:\n"
        "- If the email mentions urgency, deadlines, or critical issues, classify as important and score 4-5.\n"
        "- If it contains lottery, prizes, suspicious links, or obvious fraud, classify as spam.\n"
        "- If it mentions invoices, payments, or subscriptions, classify as bill.\n"
        "- Respond ONLY with the JSON object, no other text.\n\n"
        f"{email_text}"
    )


def build_summarize_prompt(email: dict) -> str:
    email_text = _fmt_email(email)
    return (
        "Summarize the following email in a single concise paragraph under 500 characters. "
        "Focus only on key information: who, what, when, and any action items. "
        "Do not add any commentary or labels.\n\n"
        f"{email_text}"
    )


def build_reply_prompt(email: dict, tone: str) -> str:
    tone_desc = TONES.get(tone, "Professional and polite")
    email_text = _fmt_email(email)
    return (
        f"Write a {tone} email reply ({tone_desc}) to the following email. "
        "Write only the reply body text, no subject line, no signatures, no labels.\n\n"
        f"{email_text}"
    )


def build_extract_reminders_prompt(email: dict) -> str:
    email_text = _fmt_email(email)
    return (
        "Extract any deadlines, meetings, payment reminders, reply tasks, or action items from the email below. "
        "Respond ONLY with a JSON array of reminder objects. Each object must have:\n"
        "- title (string, required)\n"
        "- description (string or null)\n"
        "- reminder_type (one of: " + REMINDER_TYPES + ")\n"
        "- due_at (ISO 8601 date string or null, e.g. \"2026-07-15T00:00:00\")\n\n"
        "If no reminders are found, respond with an empty array: []\n\n"
        "Example: [{\"title\": \"Submit report\", \"description\": \"Q3 budget due\", "
        "\"reminder_type\": \"deadline\", \"due_at\": \"2026-07-15T00:00:00\"}]\n\n"
        "Respond ONLY with the JSON array, no other text.\n\n"
        f"{email_text}"
    )
