from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.services import sync_service
from app.api.deps import require_user

router = APIRouter()


@router.post("/sync/gmail")
def trigger_gmail_sync(db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        result = sync_service.sync_gmail_inbox(db, user.id)
        return {"new": result.new, "skipped": result.skipped, "errors": result.errors}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/sync/outlook")
def trigger_outlook_sync(db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        result = sync_service.sync_outlook_inbox(db, user.id)
        return {"new": result.new, "skipped": result.skipped, "errors": result.errors}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
