from __future__ import annotations
import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.schemas import ReminderStatus


class ReminderResponse(BaseModel):
    id: int
    email_id: int
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime.datetime] = None
    reminder_type: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class ReminderListResponse(BaseModel):
    items: list[ReminderResponse]
    total: int
    page: int
    page_size: int


class ReminderPatchRequest(BaseModel):
    status: Optional[ReminderStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None


class DeleteReminderResponse(BaseModel):
    status: str


class BulkReminderRequest(BaseModel):
    reminder_ids: list[int] = Field(min_length=1, max_length=100)
    action: Literal["complete", "delete"]


class BulkReminderResponse(BaseModel):
    action: str
    requested: int
    updated: int
    not_found: int
