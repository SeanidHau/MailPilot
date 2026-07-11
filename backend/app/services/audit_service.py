"""Audit log service for user actions and AI content operations."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def log_action(
    db: Session,
    user_id: int,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    detail: Optional[str] = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(entry)
    # Commit is handled by the caller


def get_audit_logs(
    db: Session, user_id: int, page: int = 1, page_size: int = 50
):
    query = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
