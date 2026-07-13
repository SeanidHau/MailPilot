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
from app.ai.metadata import PROMPT_VERSION
from app.ai.spam import detect_spam
from app.ai.rules import should_extract_reminders

MOCK_DATA_PATH = Path(__file__).parent.parent / "mock_data" / "emails.json"
logger = logging.getLogger(__name__)


def import_mock_emails(db: Session, user_id: int, auto_process: bool = True) -> int:
    with open(MOCK_DATA_PATH) as f:
        emails_data = json.load(f)

    from datetime import datetime as dt

    imported = 0
    imported_ids: list[int] = []
    for data in emails_data:
        q = db.query(Email).filter(Email.message_id == data["message_id"], Email.user_id == user_id)
        if q.first():
            continue
        if isinstance(data.get("received_at"), str):
            data["received_at"] = dt.fromisoformat(data["received_at"])
        email = Email(**data, user_id=user_id)
        db.add(email)
        db.flush()
        imported_ids.append(email.id)
        imported += 1

    audit_service.log_action(db, user_id, "email_import", "email", None, f"imported {imported}")
    db.commit()
    if auto_process and imported_ids:
        processing_errors = process_emails_with_ai(db, user_id, imported_ids)
        if processing_errors:
            logger.warning("email_auto_processing_failed", extra={"user_id": user_id, "errors": processing_errors})
    return imported


REQUIRED_FIELDS = ["message_id", "sender", "recipients", "subject", "body", "received_at"]


def import_emails_from_list(db: Session, emails_data: list[dict], user_id: int) -> dict:
    """Import emails from a list of dicts. Returns {imported, skipped, errors}.
    Validates each item individually; bad items are skipped with errors, good items are imported."""
    from datetime import datetime as dt

    imported = 0
    skipped = 0
    errors: list[str] = []
    imported_ids: list[int] = []

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
            db.flush()
            imported_ids.append(email.id)
            imported += 1
        except Exception as exc:
            errors.append(f"Item {i} ({msg_id}): {exc}")

    audit_service.log_action(db, user_id, "email_import", "email", None, f"upload imported={imported} skipped={skipped}")
    db.commit()
    if imported_ids:
        errors.extend(process_emails_with_ai(db, user_id, imported_ids))
    return {"imported": imported, "skipped": skipped, "errors": errors}


def get_emails(
    db: Session,
    user_id: int,
    q: Optional[str] = None,
    category: Optional[str] = None,
    is_read: Optional[bool] = None,
    min_importance: Optional[int] = None,
    max_importance: Optional[int] = None,
    sort_by: str = "received_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(Email).filter(Email.user_id == user_id, Email.is_deleted.is_(False))

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
    sort_column = Email.importance_score if sort_by == "importance" else Email.received_at
    primary_order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    if sort_by == "importance":
        secondary_order = Email.received_at.desc()
    else:
        secondary_order = Email.id.asc() if sort_order == "asc" else Email.id.desc()
    items = query.order_by(primary_order, secondary_order).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_email_detail(db: Session, email_id: int, user_id: int) -> Email | None:
    return db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user_id,
        Email.is_deleted.is_(False),
    ).first()


def patch_email(db: Session, email_id: int, updates: dict, user_id: int) -> Email | None:
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user_id,
        Email.is_deleted.is_(False),
    ).first()
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


def bulk_update_emails(db: Session, email_ids: list[int], action: str, user_id: int) -> dict:
    unique_ids = list(dict.fromkeys(email_ids))
    emails = (
        db.query(Email)
        .filter(
            Email.id.in_(unique_ids),
            Email.user_id == user_id,
            Email.is_deleted.is_(False),
        )
        .all()
    )

    for email in emails:
        if action == "mark_read":
            email.is_read = True
        elif action == "delete":
            email.is_deleted = True

    updated = len(emails)
    not_found = len(unique_ids) - updated
    audit_service.log_action(
        db,
        user_id,
        f"email_bulk_{action}",
        "email",
        None,
        f"requested={len(unique_ids)} updated={updated}",
    )
    db.commit()
    return {
        "action": action,
        "requested": len(unique_ids),
        "updated": updated,
        "not_found": not_found,
    }


def classify_email(db: Session, email_id: int, user_id: int):
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user_id,
        Email.is_deleted.is_(False),
    ).first()
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
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user_id,
        Email.is_deleted.is_(False),
    ).first()
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


def process_email_with_ai(db: Session, email_id: int, user_id: int) -> list[str]:
    """Run classification, summary, and reminders in one provider request."""
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user_id,
        Email.is_deleted.is_(False),
    ).first()
    if not email:
        return [f"email {email_id}: not found"]

    provider = get_ai_provider(db, user_id)
    email_data = {"subject": email.subject, "body": email.body, "sender": email.sender}
    include_reminders = should_extract_reminders(email_data)
    result, provider_error = provider.process_email(email_data, include_reminders=include_reminders)
    errors: list[str] = []
    if provider_error:
        errors.append(f"email {email_id} AI: {provider_error.message}")

    email.category = result.get("category", "normal")
    email.importance_score = max(1, min(5, int(result.get("importance_score", 1))))
    email.summary = str(result.get("summary", "暂无可用内容。"))[:500]

    confidence, signals = detect_spam(db, user_id, email_data)
    email.spam_confidence = confidence
    email.spam_signals = json.dumps(signals) if signals else None
    if confidence > 0.5 and email.category != "important":
        email.category = "spam"

    audit_service.log_action(db, user_id, "email_classify", "email", email_id, f"{email.category} score={email.importance_score}")
    audit_service.log_action(db, user_id, "email_summarize", "email", email_id, None)

    if include_reminders and email.category not in {"spam", "promotion"} and not provider_error:
        from app.services import reminder_service

        created = reminder_service.create_reminders_from_items(
            db, email_id, user_id, result.get("reminders", []), provider, deduplicate=True,
        )
        audit_service.log_action(db, user_id, "reminder_extract", "email", email_id, f"reminder count: {len(created)}")

    # A failed run remains eligible for retry after the user fixes the AI configuration.
    email.ai_metadata = None if provider_error else make_metadata(
        provider.__class__.__name__, getattr(provider, "model", "mock"),
    )
    db.commit()
    return errors


def process_emails_with_ai(
    db: Session,
    user_id: int,
    email_ids: list[int] | None = None,
) -> list[str]:
    """Process new emails, or retry emails not handled by the current provider."""
    query = db.query(Email).filter(Email.user_id == user_id)
    if email_ids is not None:
        if not email_ids:
            return []
        query = query.filter(Email.id.in_(email_ids))

    # Resolve the current provider once so changing AI settings can trigger
    # processing for emails previously handled by a different provider.
    current_provider = get_ai_provider(db, user_id).__class__.__name__
    emails = query.order_by(Email.id.asc()).all()
    errors: list[str] = []
    for email in emails:
        if email_ids is None and email.ai_metadata:
            try:
                metadata = json.loads(email.ai_metadata)
            except (TypeError, json.JSONDecodeError):
                metadata = {}
            if (
                metadata.get("provider") == current_provider
                and metadata.get("prompt_version") == PROMPT_VERSION
            ):
                continue

        try:
            errors.extend(process_email_with_ai(db, email.id, user_id))
        except Exception as exc:
            db.rollback()
            message = f"email {email.id}: {exc}"
            errors.append(message)
            logger.exception("email_auto_processing_exception", extra={"user_id": user_id, "email_id": email.id})
    return errors


def process_unprocessed_emails(db: Session, user_id: int, progress_callback=None) -> dict:
    """Process only emails that do not have a complete AI result yet."""
    emails = (
        db.query(Email)
        .filter(
            Email.user_id == user_id,
            Email.is_deleted.is_(False),
            or_(Email.ai_metadata.is_(None), Email.summary.is_(None)),
        )
        .order_by(Email.id.asc())
        .all()
    )
    total = len(emails)
    errors: list[str] = []
    processed = 0
    failed = 0
    if progress_callback:
        progress_callback({"total": total, "processed": 0, "failed": 0, "errors": []})

    for email in emails:
        if progress_callback:
            progress_callback({
                "total": total,
                "processed": processed,
                "failed": failed,
                "current_email_id": email.id,
                "current_subject": email.subject,
                "stage": "processing",
                "errors": errors[-10:],
            })
        try:
            email_errors = process_email_with_ai(db, email.id, user_id)
            errors.extend(email_errors)
            if email_errors:
                failed += 1
        except Exception as exc:
            db.rollback()
            errors.append(f"email {email.id}: {exc}")
            failed += 1
            logger.exception(
                "email_manual_processing_exception",
                extra={"user_id": user_id, "email_id": email.id},
            )
        processed += 1
        if progress_callback:
            progress_callback({
                "total": total,
                "processed": processed,
                "failed": failed,
                "current_email_id": None,
                "current_subject": None,
                "stage": "waiting",
                "errors": errors[-10:],
            })

    return {
        "total": total,
        "processed": processed,
        "failed": failed,
        "errors": errors,
    }
