from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel


class FeedbackResponse(BaseModel):
    id: int
    email_id: int
    old_category: str
    new_category: str
    reason: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class FeedbackCreateRequest(BaseModel):
    email_id: int
    old_category: str
    new_category: str
    reason: Optional[str] = None
