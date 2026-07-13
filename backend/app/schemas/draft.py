from __future__ import annotations
import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.schemas import DraftStatus


class DraftResponse(BaseModel):
    id: int
    email_id: Optional[int]
    tone: str
    content: str
    recipient: Optional[str] = None
    subject: Optional[str] = None
    status: str
    send_error: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class DraftListResponse(BaseModel):
    items: list[DraftResponse]
    total: int
    page: int
    page_size: int


class DeleteDraftResponse(BaseModel):
    status: str


class DraftPatchRequest(BaseModel):
    content: Optional[str] = None
    recipient: Optional[str] = Field(default=None, min_length=3, max_length=512)
    subject: Optional[str] = Field(default=None, min_length=1, max_length=512)
    status: Optional[DraftStatus] = None


class DraftCreateRequest(BaseModel):
    recipient: str = Field(min_length=3, max_length=512)
    subject: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)


class SendDraftRequest(BaseModel):
    """Optional mailbox selection for sending a reply draft."""

    provider: Optional[Literal["gmail", "outlook"]] = None
