from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GmailAuthorizeResponse(BaseModel):
    authorization_url: str


class GmailStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    scopes: Optional[str] = None
    expires_at: Optional[datetime] = None


class GmailCallbackResponse(BaseModel):
    connected: bool
    email: Optional[str] = None


class GmailRefreshResponse(BaseModel):
    connected: bool
    expires_at: Optional[datetime] = None
