from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.schemas.job import JobAcceptedResponse
from app.services import job_service
from app.api.deps import require_user

router = APIRouter()


@router.post("/sync/gmail", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_gmail_sync(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    job = job_service.create_or_schedule_job(db, user.id, "gmail_sync", db.get_bind())
    return {"job_id": job.id, "status": job.status}


@router.post("/sync/outlook", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_outlook_sync(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    job = job_service.create_or_schedule_job(db, user.id, "outlook_sync", db.get_bind())
    return {"job_id": job.id, "status": job.status}
