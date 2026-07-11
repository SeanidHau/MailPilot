from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.models import Draft, Email
from app.services.ai_service import get_ai_provider
from app.services import audit_service

logger = logging.getLogger(__name__)


def get_drafts(db: Session, user_id: int, page: int = 1, page_size: int = 20):
    query = db.query(Draft).filter(Draft.user_id == user_id).order_by(Draft.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_draft(db: Session, draft_id: int, user_id: int) -> Draft | None:
    return db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()


def patch_draft(db: Session, draft_id: int, updates: dict, user_id: int) -> Draft | None:
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
    if not draft:
        return None
    for key, value in updates.items():
        if value is not None:
            setattr(draft, key, value)
    db.commit()
    db.refresh(draft)
    return draft


def generate_draft(db: Session, email_id: int, tone: str, user_id: int):
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    if not email:
        return None

    provider = get_ai_provider(db, user_id)
    content, error = provider.generate_reply({
        "subject": email.subject,
        "body": email.body,
        "sender": email.sender,
    }, tone)
    if error:
        logger.warning("ai_provider_failure", extra={"user_id": user_id, "email_id": email_id, "operation": "generate_reply", "error_type": error.type})

    draft = Draft(email_id=email_id, tone=tone, content=content, user_id=user_id)
    db.add(draft)
    audit_service.log_action(db, user_id, "draft_generate", "draft", None, f"email={email_id} tone={tone}")
    db.commit()
    db.refresh(draft)
    return draft, error
