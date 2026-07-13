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
        "你是 MailPilot 的邮件摘要助手。请阅读下面的邮件，并使用简体中文输出摘要。\n"
        "即使邮件原文是英文或其他语言，也必须先理解内容，再用自然、准确的简体中文表达。\n\n"
        "要求：\n"
        "- 只输出摘要正文，不要标题、标签、前言、结论或 Markdown 格式。\n"
        "- 使用 1-3 句简洁完整的话，控制在 300 个汉字以内，且不要超过 500 个字符。\n"
        "- 聚焦发件人和背景、核心事项、时间/地点/金额，以及用户需要采取的行动。\n"
        "- 保留姓名、公司名、专有名词、金额和日期等关键信息，不要猜测或编造原文没有的信息。\n"
        "- 如果邮件没有有效内容，只输出：暂无可用内容。\n\n"
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


def build_process_prompt(email: dict, include_reminders: bool = True) -> str:
    """Build the single-call prompt for classification, summary, and reminders."""
    cat_desc = "\n".join(f"- {c}: {d}" for c, d in CATEGORIES)
    reminder_instruction = (
        "Extract real deadlines, meetings, payments, reply tasks, or action items into reminders."
        if include_reminders
        else "Set reminders to an empty array because this email has no reminder signals."
    )
    return (
        "You are MailPilot's email processing assistant. Analyze the email below and respond ONLY with one JSON object.\n"
        "The JSON must contain exactly these fields:\n"
        "- category: one of the categories below\n"
        "- importance_score: integer from 1 to 5\n"
        "- summary: a concise Simplified Chinese summary, no Markdown, at most 300 Chinese characters\n"
        "- reminders: an array of objects with title, description, reminder_type, and due_at\n\n"
        f"Categories:\n{cat_desc}\n\n"
        f"{reminder_instruction}\n"
        "Do not invent dates or follow-up tasks. If there is no real reminder, use [].\n"
        "Preserve names, organizations, amounts, dates, and actions from the original email.\n"
        "Example: {\"category\":\"important\",\"importance_score\":4,\"summary\":\"请在周五前提交报告。\",\"reminders\":[]}\n\n"
        f"{_fmt_email(email)}"
    )
