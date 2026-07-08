from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import ClassificationFeedback


def get_feedback(db: Session, user_id: int, page: int = 1, page_size: int = 20):
    query = (
        db.query(ClassificationFeedback)
        .filter(ClassificationFeedback.user_id == user_id)
        .order_by(ClassificationFeedback.created_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
