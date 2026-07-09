from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import Email, ClassificationFeedback
from app.services.ai_service import get_ai_provider

MOCK_DATA_PATH = Path(__file__).parent.parent / "mock_data" / "emails.json"


def import_mock_emails(db: Session, user_id: int) -> int:
    with open(MOCK_DATA_PATH) as f:
        emails_data = json.load(f)

    from datetime import datetime as dt

    imported = 0
    for data in emails_data:
        q = db.query(Email).filter(Email.message_id == data["message_id"], Email.user_id == user_id)
        if q.first():
            continue
        if isinstance(data.get("received_at"), str):
            data["received_at"] = dt.fromisoformat(data["received_at"])
        email = Email(**data, user_id=user_id)
        db.add(email)
        imported += 1

    db.commit()
    return imported


def import_emails_from_list(db: Session, emails_data: list[dict], user_id: int) -> dict:
    """Import emails from a list of dicts. Returns {imported, skipped, errors}."""
    from datetime import datetime as dt

    imported = 0
    skipped = 0
    errors: list[str] = []

    for i, data in enumerate(emails_data):
        if not isinstance(data, dict):
            errors.append(f"Item {i}: not a JSON object")
            continue
        msg_id = data.get("message_id", "")
        if not msg_id:
            errors.append(f"Item {i}: missing message_id")
            continue
        q = db.query(Email).filter(Email.message_id == msg_id, Email.user_id == user_id)
        if q.first():
            skipped += 1
            continue
        try:
            if isinstance(data.get("received_at"), str):
                data["received_at"] = dt.fromisoformat(data["received_at"])
            email = Email(
                message_id=msg_id,
                sender=data.get("sender", ""),
                recipients=data.get("recipients", ""),
                subject=data.get("subject", ""),
                body=data.get("body", ""),
                received_at=data["received_at"],
                user_id=user_id,
            )
            db.add(email)
            imported += 1
        except Exception as exc:
            errors.append(f"Item {i} ({msg_id}): {exc}")

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}


def get_emails(
    db: Session,
    user_id: int,
    q: Optional[str] = None,
    category: Optional[str] = None,
    is_read: Optional[bool] = None,
    min_importance: Optional[int] = None,
    max_importance: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(Email).filter(Email.user_id == user_id)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Email.subject.ilike(like), Email.sender.ilike(like), Email.body.ilike(like))
        )
    if category:
        query = query.filter(Email.category == category)
    if is_read is not None:
        query = query.filter(Email.is_read == is_read)
    if min_importance is not None:
        query = query.filter(Email.importance_score >= min_importance)
    if max_importance is not None:
        query = query.filter(Email.importance_score <= max_importance)

    total = query.count()
    items = query.order_by(Email.received_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_email_detail(db: Session, email_id: int, user_id: int) -> Email | None:
    return db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()


def patch_email(db: Session, email_id: int, updates: dict, user_id: int) -> Email | None:
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    if not email:
        return None

    old_category = email.category
    for key, value in updates.items():
        if value is not None:
            setattr(email, key, value)

    if "category" in updates and updates["category"] is not None and updates["category"] != old_category:
        fb = ClassificationFeedback(
            email_id=email.id,
            old_category=old_category,
            new_category=updates["category"],
            user_id=user_id,
        )
        db.add(fb)

    db.commit()
    db.refresh(email)
    return email


def classify_email(db: Session, email_id: int, user_id: int):
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    if not email:
        return None

    provider = get_ai_provider(db, user_id)
    category, score = provider.classify_email({
        "subject": email.subject,
        "body": email.body,
        "sender": email.sender,
    })

    email.category = category
    email.importance_score = score
    db.commit()
    db.refresh(email)
    return email


def summarize_email(db: Session, email_id: int, user_id: int):
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    if not email:
        return None

    provider = get_ai_provider(db, user_id)
    summary = provider.summarize_email({
        "subject": email.subject,
        "body": email.body,
    })

    email.summary = summary
    db.commit()
    db.refresh(email)
    return email
