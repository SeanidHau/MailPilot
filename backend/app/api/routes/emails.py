from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.email import ImportResponse, EmailResponse, EmailListResponse, EmailPatchRequest, EmailDetailResponse
from app.schemas.ai import ClassifyResponse, SummarizeResponse, GenerateDraftRequest, GenerateDraftResponse, ExtractRemindersResponse
from app.services import email_service, draft_service, reminder_service
from app.api.deps import get_current_user

router = APIRouter()


def _uid(user) -> Optional[int]:
    return user.id if user else None


@router.post("/emails/import", response_model=ImportResponse)
def import_emails(db: Session = Depends(get_db), user=Depends(get_current_user)):
    count = email_service.import_mock_emails(db, _uid(user))
    return {"imported": count}


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
    user=Depends(get_current_user),
):
    items, total = email_service.get_emails(
        db, user_id=_uid(user), q=q, category=category, is_read=is_read,
        min_importance=min_importance, max_importance=max_importance,
        page=page, page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/emails/{email_id}", response_model=EmailDetailResponse)
def get_email(email_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    email = email_service.get_email_detail(db, email_id, _uid(user))
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.patch("/emails/{email_id}", response_model=EmailResponse)
def patch_email(email_id: int, body: EmailPatchRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    email = email_service.patch_email(db, email_id, body.model_dump(exclude_unset=True), _uid(user))
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/emails/{email_id}/classify", response_model=ClassifyResponse)
def classify_email(email_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    email = email_service.classify_email(db, email_id, _uid(user))
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"category": email.category, "importance_score": email.importance_score}


@router.post("/emails/{email_id}/summarize", response_model=SummarizeResponse)
def summarize_email(email_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    email = email_service.summarize_email(db, email_id, _uid(user))
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"summary": email.summary}


@router.post("/emails/{email_id}/drafts", response_model=GenerateDraftResponse)
def create_draft(email_id: int, body: GenerateDraftRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    draft = draft_service.generate_draft(db, email_id, body.tone.value, _uid(user))
    if not draft:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"id": draft.id, "tone": draft.tone, "content": draft.content}


@router.post("/emails/{email_id}/reminders/extract", response_model=ExtractRemindersResponse)
def extract_reminders(email_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    items = reminder_service.extract_reminders(db, email_id, _uid(user))
    if items is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return {
        "reminders": [
            {
                "title": r.title,
                "description": r.description,
                "reminder_type": r.reminder_type,
                "due_at": r.due_at.isoformat() if r.due_at else None,
            }
            for r in items
        ]
    }
