from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_user
from app.db.session import get_db
from app.schemas.job import JobResponse
from app.services import job_service

router = APIRouter()


@router.get("/jobs/active", response_model=Optional[JobResponse])
def get_active_job(
    job_type: str = Query("ai_process"),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    job = job_service.get_active_job(db, user.id, job_type)
    return job_service.serialize_job(job) if job else None


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    job = job_service.get_job(db, job_id, user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_service.serialize_job(job)


@router.post("/jobs/{job_id}/pause", response_model=JobResponse)
def pause_job(job_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    try:
        job = job_service.request_pause_job(db, job_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_service.serialize_job(job)
