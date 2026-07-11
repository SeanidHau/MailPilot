from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import Email, ClassificationFeedback
from app.services.ai_service import get_ai_provider
from app.services import audit_service
from app.ai.metadata import make_metadata
from app.ai.spam import detect_spam

MOCK_DATA_PATH = Path(__file__).parent.parent / "mock_data" / "emails.json"
logger = logging.getLogger(__name__)


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

    audit_service.log_action(db, user_id, "email_import", "email", None, f"imported {imported}")
    db.commit()
    return imported


REQUIRED_FIELDS = ["message_id", "sender", "recipients", "subject", "body", "received_at"]


def import_emails_from_list(db: Session, emails_data: list[dict], user_id: int) -> dict:
    """Import emails from a list of dicts. Returns {imported, skipped, errors}.
    Validates each item individually; bad items are skipped with errors, good items are imported."""
    from datetime import datetime as dt

    imported = 0
    skipped = 0
    errors: list[str] = []

    for i, data in enumerate(emails_data):
        if not isinstance(data, dict):
            errors.append(f"Item {i}: not a JSON object")
            continue

        # Validate required fields
        missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
        if missing:
            errors.append(f"Item {i} ({data.get('message_id', 'no id')}): missing required fields: {', '.join(missing)}")
            continue

        msg_id = data["message_id"]

        # Deduplicate per user
        q = db.query(Email).filter(Email.message_id == msg_id, Email.user_id == user_id)
        if q.first():
            skipped += 1
            continue

        try:
            if isinstance(data.get("received_at"), str):
                data["received_at"] = dt.fromisoformat(data["received_at"])
            email = Email(
                message_id=msg_id,
                sender=data["sender"],
                recipients=data["recipients"],
                subject=data["subject"],
                body=data["body"],
                received_at=data["received_at"],
                user_id=user_id,
            )
            db.add(email)
            imported += 1
        except Exception as exc:
            errors.append(f"Item {i} ({msg_id}): {exc}")

    audit_service.log_action(db, user_id, "email_import", "email", None, f"upload imported={imported} skipped={skipped}")
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
        audit_service.log_action(db, user_id, "category_change", "email", email_id, f"{old_category}->{updates['category']}")

    db.commit()
    db.refresh(email)
    return email


def classify_email(db: Session, email_id: int, user_id: int):
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    if not email:
        return None

    provider = get_ai_provider(db, user_id)
    category, score, error = provider.classify_email({
        "subject": email.subject,
        "body": email.body,
        "sender": email.sender,
    })
    if error:
        logger.warning("ai_provider_failure", extra={"user_id": user_id, "email_id": email_id, "operation": "classify", "error_type": error.type})

    email.category = category
    email.importance_score = score
    email.ai_metadata = make_metadata(provider.__class__.__name__, getattr(provider, 'model', 'mock'))

    # Spam detection: run multi-signal analysis
    confidence, signals = detect_spam(db, user_id, {"subject": email.subject, "body": email.body, "sender": email.sender})
    email.spam_confidence = confidence
    email.spam_signals = json.dumps(signals) if signals else None
    if confidence > 0.5 and category != "important":
        email.category = "spam"

    audit_service.log_action(db, user_id, "email_classify", "email", email_id, f"{category} score={score}")
    db.commit()
    db.refresh(email)
    return email, error


def summarize_email(db: Session, email_id: int, user_id: int):
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    if not email:
        return None

    provider = get_ai_provider(db, user_id)
    summary, error = provider.summarize_email({
        "subject": email.subject,
        "body": email.body,
    })
    if error:
        logger.warning("ai_provider_failure", extra={"user_id": user_id, "email_id": email_id, "operation": "summarize", "error_type": error.type})

    email.summary = summary
    email.ai_metadata = make_metadata(provider.__class__.__name__, getattr(provider, 'model', 'mock'))
    audit_service.log_action(db, user_id, "email_summarize", "email", email_id, None)
    db.commit()
    db.refresh(email)
    return email, error
