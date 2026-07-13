from __future__ import annotations
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Reminder, Email
from app.services.ai_service import get_ai_provider
from app.services import audit_service
from app.ai.metadata import make_metadata

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


def bulk_update_reminders(db: Session, reminder_ids: list[int], action: str, user_id: int) -> dict:
    unique_ids = list(dict.fromkeys(reminder_ids))
    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.id.in_(unique_ids),
            Reminder.user_id == user_id,
            Reminder.status != "deleted",
        )
        .all()
    )

    updated = 0
    for reminder in reminders:
        if action == "complete" and reminder.status == "pending":
            reminder.status = "done"
            updated += 1
        elif action == "delete":
            reminder.status = "deleted"
            updated += 1

    audit_service.log_action(
        db,
        user_id,
        f"reminder_bulk_{action}",
        "reminder",
        None,
        f"requested={len(unique_ids)} updated={updated}",
    )
    db.commit()
    return {
        "action": action,
        "requested": len(unique_ids),
        "updated": updated,
        "not_found": len(unique_ids) - len(reminders),
    }


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

    created = create_reminders_from_items(db, email_id, user_id, items, provider)
    return created, error


def create_reminders_from_items(
    db: Session,
    email_id: int,
    user_id: int,
    items: list[dict],
    provider,
    deduplicate: bool = False,
):
    """Persist reminders returned by a combined AI processing request."""
    from datetime import datetime as dt

    existing = set()
    if deduplicate:
        existing = {
            (r.title, r.reminder_type, r.due_at)
            for r in db.query(Reminder).filter(
                Reminder.email_id == email_id,
                Reminder.user_id == user_id,
                Reminder.status != "deleted",
            ).all()
        }
    created = []
    for item in items:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        due_at = item.get("due_at")
        if isinstance(due_at, str):
            try:
                due_at = dt.fromisoformat(due_at)
            except (ValueError, TypeError):
                due_at = None

        reminder_type = str(item.get("reminder_type", "other"))
        key = (str(item["title"])[:256], reminder_type, due_at)
        if key in existing:
            continue
        existing.add(key)
        md = make_metadata(provider.__class__.__name__, getattr(provider, 'model', 'mock'))
        reminder = Reminder(
            email_id=email_id,
            title=key[0],
            description=item.get("description"),
            due_at=due_at,
            reminder_type=reminder_type,
            user_id=user_id,
            ai_metadata=md,
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
        extra={"user_id": user_id, "email_id": email_id, "created": len(created)},
    )
    return created
