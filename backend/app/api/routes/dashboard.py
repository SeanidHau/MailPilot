from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import DashboardSummary
from app.services import dashboard_service
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return dashboard_service.get_dashboard_summary(db, user.id if user else None)
