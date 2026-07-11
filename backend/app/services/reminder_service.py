from __future__ import annotations
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Reminder, Email
from app.services.ai_service import get_ai_provider
from app.services import audit_service

logger = logging.getLogger(__name__)


def get_reminders(db: Session, user_id: int, status: Optional[str] = None, page: int = 1, page_size: int = 20):
    query = db.query(Reminder).filter(Reminder.user_id == user_id)
    if status:
        query = query.filter(Reminder.status == status)
    else:
        query = query.filter(Reminder.status != "deleted")
    total = query.count()
    items = query.order_by(Reminder.due_at.asc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_reminder(db: Session, reminder_id: int, user_id: int) -> Reminder | None:
    return db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user_id).first()


def patch_reminder(db: Session, reminder_id: int, updates: dict, user_id: int) -> Reminder | None:
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user_id).first()
    if not reminder:
        return None
    for key, value in updates.items():
        if value is not None:
            setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder_id: int, user_id: int):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user_id).first()
    if not reminder:
        return None
    reminder.status = "deleted"
    db.commit()
    return reminder


def extract_reminders(db: Session, email_id: int, user_id: int):
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    if not email:
        return None

    provider = get_ai_provider(db, user_id)
    items, error = provider.extract_reminders({
        "subject": email.subject,
        "body": email.body,
    })
    if error:
        logger.warning("ai_provider_failure", extra={"user_id": user_id, "email_id": email_id, "operation": "extract_reminders", "error_type": error.type})

    from datetime import datetime as dt

    created = []
    for item in items:
        due_at = item.get("due_at")
        if isinstance(due_at, str):
            try:
                due_at = dt.fromisoformat(due_at)
            except (ValueError, TypeError):
                due_at = None

        reminder = Reminder(
            email_id=email_id,
            title=item["title"],
            description=item.get("description"),
            due_at=due_at,
            reminder_type=item["reminder_type"],
            user_id=user_id,
        )
        db.add(reminder)
        created.append(reminder)

    db.flush()  # get reminder ids
    reminder_ids = [r.id for r in created]
    audit_service.log_action(db, user_id, "reminder_extract", "email", email_id, f"reminder ids: {reminder_ids}")
    db.commit()
    for r in created:
        db.refresh(r)
    logger.info(
        "reminder_extraction_count",
        extra={"user_id": user_id, "email_id": email_id, "created": len(created), "provider_error": bool(error)},
    )
    return created, error
