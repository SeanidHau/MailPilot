from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.feedback import FeedbackListResponse
from app.services import feedback_service
from app.api.deps import require_user

router = APIRouter()


@router.get("/feedback", response_model=FeedbackListResponse)
def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    items, total = feedback_service.get_feedback(db, user.id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
