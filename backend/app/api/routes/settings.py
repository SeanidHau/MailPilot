from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.schemas.settings import AIProviderConfig, AISettingsUpdateResponse
from app.services import settings_service, ai_service, email_service
from app.services import job_service, task_runner
from app.api.deps import get_current_user, require_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/settings/ai", response_model=AIProviderConfig)
def get_ai_settings(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    return settings_service.get_ai_config(db, user.id if user else None)


@router.put("/settings/ai", response_model=AISettingsUpdateResponse)
def update_ai_settings(
    body: AIProviderConfig,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    result = settings_service.save_ai_config(db, body.model_dump(), user.id)
    ai_service.reset_ai_provider()
    job = job_service.create_or_get_active_job(db, user.id, "ai_process")
    if job.status == "queued":
        task_runner.schedule_job(job.id, user.id, job.job_type, db.get_bind())
    logger.info("email_ai_processing_after_settings_queued", extra={"user_id": user.id, "job_id": job.id})
    return {**result, "job_id": job.id, "job_status": job.status}
