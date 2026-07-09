from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_emails: int
    pending_emails: int
    important_emails: int
    pending_reminders: int
    recent_important_emails: list["EmailSummary"]
    upcoming_reminders: list["ReminderSummary"]


class EmailSummary(BaseModel):
    id: int
    sender: str
    subject: str
    category: str
    importance_score: int
    received_at: str

    model_config = {"from_attributes": True}


class ReminderSummary(BaseModel):
    id: int
    title: str
    reminder_type: str
    due_at: Optional[str] = None
    email_subject: str

    model_config = {"from_attributes": True}
