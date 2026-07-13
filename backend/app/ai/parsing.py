import json
import re
from typing import Any


VALID_CATEGORIES = {"important", "normal", "promotion", "bill", "school_work", "needs_reply", "spam"}


def parse_json_response(text: str) -> Any:
    """Parse JSON from LLM response, handling markdown code fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return json.loads(cleaned)


def parse_process_response(text: str) -> dict[str, Any]:
    """Parse and normalize the combined AI response."""
    data = parse_json_response(text)
    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object")

    category = str(data.get("category", "normal"))
    if category not in VALID_CATEGORIES:
        category = "normal"
    try:
        score = max(1, min(5, int(data.get("importance_score", 1))))
    except (TypeError, ValueError):
        score = 1

    summary = str(data.get("summary", "")).strip()[:500] or "暂无可用内容。"
    reminders = data.get("reminders", [])
    if not isinstance(reminders, list):
        reminders = []
    normalized_reminders = []
    for item in reminders:
        if not isinstance(item, dict) or not str(item.get("title", "")).strip():
            continue
        normalized_reminders.append({
            "title": str(item["title"])[:256],
            "description": item.get("description"),
            "reminder_type": str(item.get("reminder_type", "other")),
            "due_at": item.get("due_at"),
        })
    return {
        "category": category,
        "importance_score": score,
        "summary": summary,
        "reminders": normalized_reminders,
    }
