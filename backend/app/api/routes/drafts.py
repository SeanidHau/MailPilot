from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.draft import DraftResponse, DraftPatchRequest
from app.services import draft_service

router = APIRouter()


@router.get("/drafts")
def list_drafts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = draft_service.get_drafts(db, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = draft_service.get_draft(db, draft_id)
    if not draft:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.patch("/drafts/{draft_id}", response_model=DraftResponse)
def patch_draft(draft_id: int, body: DraftPatchRequest, db: Session = Depends(get_db)):
    draft = draft_service.patch_draft(db, draft_id, body.model_dump(exclude_unset=True))
    if not draft:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft
