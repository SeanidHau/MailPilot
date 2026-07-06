from sqlalchemy.orm import Session

from app.db.models import ClassificationFeedback


def get_feedback(db: Session, page: int = 1, page_size: int = 20):
    query = db.query(ClassificationFeedback).order_by(ClassificationFeedback.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
