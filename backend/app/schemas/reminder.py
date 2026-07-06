from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel


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


class ReminderPatchRequest(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
