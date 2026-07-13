from __future__ import annotations

import datetime
from typing import Any, Optional

from pydantic import BaseModel


class JobAcceptedResponse(BaseModel):
    job_id: int
    status: str


class JobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    finished_at: Optional[datetime.datetime] = None

