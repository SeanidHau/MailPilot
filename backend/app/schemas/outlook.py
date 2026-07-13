from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel


class OutlookAuthorizeResponse(BaseModel):
    authorization_url: str


class OutlookStatusResponse(BaseModel):
    connected: bool
    configured: bool = False
    email: Optional[str] = None
    scopes: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None
