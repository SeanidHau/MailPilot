from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from app.schemas import DraftTone


class AIError(BaseModel):
    message: str
    type: str = "provider_error"  # provider_error, timeout, rate_limit, auth_error
    retryable: bool = False


class ClassifyResponse(BaseModel):
    category: str
    importance_score: int
    error: Optional[AIError] = None


class SummarizeResponse(BaseModel):
    summary: str
    error: Optional[AIError] = None


class GenerateDraftRequest(BaseModel):
    tone: DraftTone


class GenerateDraftResponse(BaseModel):
    id: int
    tone: str
    content: str
    error: Optional[AIError] = None


class ExtractRemindersResponse(BaseModel):
    reminders: list[ReminderItem]
    error: Optional[AIError] = None


class ReminderItem(BaseModel):
    title: str
    description: Optional[str] = None
    reminder_type: str
    due_at: Optional[str] = None
