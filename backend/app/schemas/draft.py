from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel

from app.schemas import DraftStatus


class DraftResponse(BaseModel):
    id: int
    email_id: int
    tone: str
    content: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class DraftListResponse(BaseModel):
    items: list[DraftResponse]
    total: int
    page: int
    page_size: int


class DraftPatchRequest(BaseModel):
    content: Optional[str] = None
    status: Optional[DraftStatus] = None
