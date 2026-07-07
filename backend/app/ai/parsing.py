import json
import re
from typing import Any


def parse_json_response(text: str) -> Any:
    """Parse JSON from LLM response, handling markdown code fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return json.loads(cleaned)
