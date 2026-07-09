from __future__ import annotations
from typing import Optional

from typing import Any

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.email import ImportResponse, EmailResponse, EmailListResponse, EmailPatchRequest, EmailDetailResponse
from app.schemas.ai import ClassifyResponse, SummarizeResponse, GenerateDraftRequest, GenerateDraftResponse, ExtractRemindersResponse
from app.services import email_service, draft_service, reminder_service
from app.api.deps import require_user

router = APIRouter()


@router.post("/emails/import", response_model=ImportResponse)
def import_emails(db: Session = Depends(get_db), user=Depends(require_user)):
    count = email_service.import_mock_emails(db, user.id)
    return {"imported": count}


@router.post("/emails/import/upload", response_model=ImportResponse)
def import_emails_upload(body: Any = Body(...), db: Session = Depends(get_db), user=Depends(require_user)):
    if not isinstance(body, list):
        raise HTTPException(status_code=422, detail="Request body must be a JSON array of email objects")
    result = email_service.import_emails_from_list(db, body, user.id)
    return result


@router.get("/emails", response_model=EmailListResponse)
def list_emails(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    min_importance: Optional[int] = Query(None),
    max_importance: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    items, total = email_service.get_emails(
        db, user_id=user.id, q=q, category=category, is_read=is_read,
        min_importance=min_importance, max_importance=max_importance,
        page=page, page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/emails/{email_id}", response_model=EmailDetailResponse)
def get_email(email_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    email = email_service.get_email_detail(db, email_id, user.id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.patch("/emails/{email_id}", response_model=EmailResponse)
def patch_email(email_id: int, body: EmailPatchRequest, db: Session = Depends(get_db), user=Depends(require_user)):
    email = email_service.patch_email(db, email_id, body.model_dump(exclude_unset=True), user.id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/emails/{email_id}/classify", response_model=ClassifyResponse)
def classify_email(email_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    result = email_service.classify_email(db, email_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Email not found")
    email, error = result
    return {"category": email.category, "importance_score": email.importance_score, "error": error}


@router.post("/emails/{email_id}/summarize", response_model=SummarizeResponse)
def summarize_email(email_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    result = email_service.summarize_email(db, email_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Email not found")
    email, error = result
    return {"summary": email.summary, "error": error}


@router.post("/emails/{email_id}/drafts", response_model=GenerateDraftResponse)
def create_draft(email_id: int, body: GenerateDraftRequest, db: Session = Depends(get_db), user=Depends(require_user)):
    result = draft_service.generate_draft(db, email_id, body.tone.value, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Email not found")
    draft, error = result
    return {"id": draft.id, "tone": draft.tone, "content": draft.content, "error": error}


@router.post("/emails/{email_id}/reminders/extract", response_model=ExtractRemindersResponse)
def extract_reminders(email_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    result = reminder_service.extract_reminders(db, email_id, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Email not found")
    items, error = result
    return {
        "reminders": [
            {
                "title": r.title,
                "description": r.description,
                "reminder_type": r.reminder_type,
                "due_at": r.due_at.isoformat() if r.due_at else None,
            }
            for r in items
        ],
        "error": error,
    }
