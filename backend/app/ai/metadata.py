"""AI prompt version and metadata tracking."""
from __future__ import annotations

import json
from datetime import datetime, timezone

PROMPT_VERSION = "1.0.0"


def make_metadata(provider: str, model: str) -> str:
    return json.dumps({
        "prompt_version": PROMPT_VERSION,
        "provider": provider,
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
