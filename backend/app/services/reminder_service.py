from __future__ import annotations
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Reminder, Email
from app.services.ai_service import get_ai_provider


def get_reminders(db: Session, user_id: Optional[int] = None, status: Optional[str] = None, page: int = 1, page_size: int = 20):
    query = db.query(Reminder)
    if user_id is not None:
        query = query.filter(Reminder.user_id == user_id)
    if status:
        query = query.filter(Reminder.status == status)
    else:
        query = query.filter(Reminder.status != "deleted")
    total = query.count()
    items = query.order_by(Reminder.due_at.asc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_reminder(db: Session, reminder_id: int, user_id: Optional[int] = None) -> Reminder | None:
    query = db.query(Reminder).filter(Reminder.id == reminder_id)
    if user_id is not None:
        query = query.filter(Reminder.user_id == user_id)
    return query.first()


def patch_reminder(db: Session, reminder_id: int, updates: dict, user_id: Optional[int] = None) -> Reminder | None:
    query = db.query(Reminder).filter(Reminder.id == reminder_id)
    if user_id is not None:
        query = query.filter(Reminder.user_id == user_id)
    reminder = query.first()
    if not reminder:
        return None
    for key, value in updates.items():
        if value is not None:
            setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder_id: int, user_id: Optional[int] = None):
    query = db.query(Reminder).filter(Reminder.id == reminder_id)
    if user_id is not None:
        query = query.filter(Reminder.user_id == user_id)
    reminder = query.first()
    if not reminder:
        return None
    reminder.status = "deleted"
    db.commit()
    return reminder


def extract_reminders(db: Session, email_id: int, user_id: int | None = None):
    query = db.query(Email).filter(Email.id == email_id)
    if user_id is not None:
        query = query.filter(Email.user_id == user_id)
    email = query.first()
    if not email:
        return None

    provider = get_ai_provider(db, user_id)
    items = provider.extract_reminders({
        "subject": email.subject,
        "body": email.body,
    })

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

    db.commit()
    for r in created:
        db.refresh(r)
    return created
