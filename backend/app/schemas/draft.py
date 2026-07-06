from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel


class DraftResponse(BaseModel):
    id: int
    email_id: int
    tone: str
    content: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class DraftPatchRequest(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
