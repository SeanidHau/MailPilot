from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import BackgroundJob
from app.services import email_service, sync_service

logger = logging.getLogger(__name__)
ACTIVE_JOB_STATUSES = ("queued", "running", "pause_requested")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_job(db: Session, user_id: int, job_type: str) -> BackgroundJob:
    job = BackgroundJob(user_id=user_id, job_type=job_type, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_or_get_active_job(db: Session, user_id: int, job_type: str) -> BackgroundJob:
    active = (
        db.query(BackgroundJob)
        .filter(
            BackgroundJob.user_id == user_id,
            BackgroundJob.job_type == job_type,
            BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .order_by(BackgroundJob.id.desc())
        .first()
    )
    return active or create_job(db, user_id, job_type)


def get_job(db: Session, job_id: int, user_id: int) -> BackgroundJob | None:
    return (
        db.query(BackgroundJob)
        .filter(BackgroundJob.id == job_id, BackgroundJob.user_id == user_id)
        .first()
    )


def get_active_job(db: Session, user_id: int, job_type: str) -> BackgroundJob | None:
    return (
        db.query(BackgroundJob)
        .filter(
            BackgroundJob.user_id == user_id,
            BackgroundJob.job_type == job_type,
            BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .order_by(BackgroundJob.id.desc())
        .first()
    )


def create_or_schedule_job(
    db: Session,
    user_id: int,
    job_type: str,
    bind: Any,
    payload: list[dict] | None = None,
) -> BackgroundJob:
    """Create and schedule a job, or return the active one for idempotent actions."""
    active = get_active_job(db, user_id, job_type)
    if active:
        return active

    job = create_job(db, user_id, job_type)
    from app.services import task_runner

    task_runner.schedule_job(job.id, user_id, job.job_type, bind, payload)
    db.refresh(job)
    return job


def queue_ai_processing_job(db: Session, user_id: int, bind: Any) -> BackgroundJob:
    """Queue AI processing unless one is already active for this user."""
    active = get_active_job(db, user_id, "ai_process")
    if active:
        return active

    job = create_job(db, user_id, "ai_process")
    from app.services import task_runner

    task_runner.schedule_job(job.id, user_id, job.job_type, bind)
    return job


def request_pause_job(db: Session, job_id: int, user_id: int) -> BackgroundJob | None:
    job = get_job(db, job_id, user_id)
    if not job:
        return None
    if job.job_type != "ai_process":
        raise ValueError("Only AI processing jobs can be paused")
    if job.status == "queued":
        job.status = "pause_requested"
    elif job.status == "running":
        job.status = "pause_requested"
    elif job.status not in {"pause_requested", "paused", "completed", "failed"}:
        raise ValueError(f"Cannot pause job in status {job.status}")
    db.commit()
    db.refresh(job)
    return job


def recover_stale_jobs(db: Session) -> int:
    """Mark jobs left active by a previous worker process as failed."""
    stale_jobs = db.query(BackgroundJob).filter(
        BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
    ).all()
    if not stale_jobs:
        return 0

    now = _utcnow()
    for job in stale_jobs:
        job.status = "failed"
        job.error = "后台工作进程已重启，任务未完成，请重新提交。"
        job.finished_at = now
    db.commit()
    logger.warning("recovered_stale_background_jobs", extra={"count": len(stale_jobs)})
    return len(stale_jobs)


def serialize_job(job: BackgroundJob) -> dict[str, Any]:
    result = None
    if job.result:
        try:
            result = json.loads(job.result)
        except (TypeError, json.JSONDecodeError):
            result = {"raw": job.result}
    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "result": result,
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


def run_job(
    job_id: int,
    user_id: int,
    job_type: str,
    bind: Any,
    payload: list[dict] | None = None,
) -> None:
    """Execute a queued job using a fresh session in the worker thread."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=bind)
    db = SessionLocal()
    try:
        job = db.query(BackgroundJob).filter(
            BackgroundJob.id == job_id,
            BackgroundJob.user_id == user_id,
        ).first()
        if not job:
            return
        if job.status == "pause_requested":
            job.status = "paused"
            job.result = json.dumps({
                "total": 0,
                "processed": 0,
                "failed": 0,
                "paused": True,
                "errors": [],
            }, ensure_ascii=False)
            job.finished_at = _utcnow()
            db.commit()
            return

        job.status = "running"
        job.started_at = _utcnow()
        db.commit()

        if job_type == "email_import":
            result = {
                "imported": email_service.import_mock_emails(db, user_id),
                "skipped": 0,
                "errors": [],
            }
        elif job_type == "email_upload":
            result = email_service.import_emails_from_list(db, payload or [], user_id)
        elif job_type == "gmail_sync":
            sync_result = sync_service.sync_gmail_inbox(db, user_id)
            result = {
                "new": sync_result.new,
                "skipped": sync_result.skipped,
                "errors": sync_result.errors,
            }
            if sync_result.new > 0:
                ai_job = queue_ai_processing_job(db, user_id, bind)
                result["ai_job_id"] = ai_job.id
        elif job_type == "outlook_sync":
            sync_result = sync_service.sync_outlook_inbox(db, user_id)
            result = {
                "new": sync_result.new,
                "skipped": sync_result.skipped,
                "errors": sync_result.errors,
            }
            if sync_result.new > 0:
                ai_job = queue_ai_processing_job(db, user_id, bind)
                result["ai_job_id"] = ai_job.id
        elif job_type == "ai_process":
            def update_progress(progress: dict[str, Any]) -> None:
                current = db.query(BackgroundJob).filter(
                    BackgroundJob.id == job_id,
                    BackgroundJob.user_id == user_id,
                ).one()
                current.result = json.dumps(progress, ensure_ascii=False)
                db.commit()

            def should_pause() -> bool:
                current = db.query(BackgroundJob).filter(
                    BackgroundJob.id == job_id,
                    BackgroundJob.user_id == user_id,
                ).one()
                return current.status == "pause_requested"

            result = email_service.process_unprocessed_emails(
                db, user_id, progress_callback=update_progress, should_pause=should_pause,
            )
        else:
            raise ValueError(f"Unknown background job type: {job_type}")

        job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).one()
        job.status = "paused" if result.get("paused") else "completed"
        job.result = json.dumps(result, ensure_ascii=False)
        job.finished_at = _utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("background_job_failed", extra={"job_id": job_id, "user_id": user_id})
        job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.finished_at = _utcnow()
            db.commit()
    finally:
        db.close()
