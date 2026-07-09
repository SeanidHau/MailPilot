from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.draft import DraftResponse, DraftListResponse, DraftPatchRequest
from app.services import draft_service, mail_send_service
from app.api.deps import require_user

router = APIRouter()


@router.get("/drafts", response_model=DraftListResponse)
def list_drafts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    items, total = draft_service.get_drafts(db, user_id=user.id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    draft = draft_service.get_draft(db, draft_id, user.id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.patch("/drafts/{draft_id}", response_model=DraftResponse)
def patch_draft(draft_id: int, body: DraftPatchRequest, db: Session = Depends(get_db), user=Depends(require_user)):
    draft = draft_service.patch_draft(db, draft_id, body.model_dump(exclude_unset=True), user.id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post("/drafts/{draft_id}/send", response_model=DraftResponse)
def send_draft(draft_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    try:
        draft = mail_send_service.send_draft(db, draft_id, user.id)
        return draft
    except mail_send_service.SendError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
