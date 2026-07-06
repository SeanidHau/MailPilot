from __future__ import annotations
from sqlalchemy.orm import Session

from app.db.models import Draft, Email
from app.services.ai_service import get_ai_provider


def get_drafts(db: Session, page: int = 1, page_size: int = 20):
    query = db.query(Draft).order_by(Draft.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_draft(db: Session, draft_id: int) -> Draft | None:
    return db.query(Draft).filter(Draft.id == draft_id).first()


def patch_draft(db: Session, draft_id: int, updates: dict) -> Draft | None:
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        return None
    for key, value in updates.items():
        if value is not None:
            setattr(draft, key, value)
    db.commit()
    db.refresh(draft)
    return draft


def generate_draft(db: Session, email_id: int, tone: str):
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        return None

    provider = get_ai_provider()
    content = provider.generate_reply({
        "subject": email.subject,
        "body": email.body,
        "sender": email.sender,
    }, tone)

    draft = Draft(email_id=email_id, tone=tone, content=content)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
