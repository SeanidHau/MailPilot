from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas import EmailCategory


class ImportResponse(BaseModel):
    imported: int
    skipped: int = 0
    errors: list[str] = []


class EmailBase(BaseModel):
    sender: str
    recipients: str
    subject: str
    body: str
    received_at: datetime.datetime


class EmailResponse(BaseModel):
    id: int
    message_id: str
    sender: str
    recipients: str
    subject: str
    body: str
    received_at: datetime.datetime
    is_read: bool
    category: str
    importance_score: int
    summary: Optional[str] = None
    spam_confidence: Optional[float] = None
    spam_signals: Optional[str] = None
    imported_source: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class EmailListResponse(BaseModel):
    items: list[EmailResponse]
    total: int
    page: int
    page_size: int


class EmailPatchRequest(BaseModel):
    is_read: Optional[bool] = None
    category: Optional[EmailCategory] = None
    importance_score: Optional[int] = Field(None, ge=1, le=5)


class EmailDetailResponse(EmailResponse):
    drafts: list[DraftResponse] = []
    reminders: list[ReminderResponse] = []


from app.schemas.draft import DraftResponse  # noqa: E402
from app.schemas.reminder import ReminderResponse  # noqa: E402
EmailDetailResponse.model_rebuild()
