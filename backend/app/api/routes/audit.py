from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import audit_service
from app.api.deps import require_user

router = APIRouter()


@router.get("/audit")
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    items, total = audit_service.get_audit_logs(db, user.id, page=page, page_size=page_size)
    return {
        "items": [
            {
                "id": e.id,
                "action": e.action,
                "target_type": e.target_type,
                "target_id": e.target_id,
                "detail": e.detail,
                "created_at": e.created_at.isoformat(),
            }
            for e in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
