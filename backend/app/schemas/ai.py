from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from app.schemas import DraftTone


class ClassifyResponse(BaseModel):
    category: str
    importance_score: int


class SummarizeResponse(BaseModel):
    summary: str


class GenerateDraftRequest(BaseModel):
    tone: DraftTone


class GenerateDraftResponse(BaseModel):
    id: int
    tone: str
    content: str


class ExtractRemindersResponse(BaseModel):
    reminders: list[ReminderItem]


class ReminderItem(BaseModel):
    title: str
    description: Optional[str] = None
    reminder_type: str
    due_at: Optional[str] = None
