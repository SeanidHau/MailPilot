from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reminder import ReminderResponse, ReminderListResponse, ReminderPatchRequest, DeleteReminderResponse
from app.services import reminder_service
from app.api.deps import require_user

router = APIRouter()


@router.get("/reminders", response_model=ReminderListResponse)
def list_reminders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    items, total = reminder_service.get_reminders(db, user_id=user.id, status=status, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/reminders/{reminder_id}", response_model=ReminderResponse)
def get_reminder(reminder_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    reminder = reminder_service.get_reminder(db, reminder_id, user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse)
def patch_reminder(reminder_id: int, body: ReminderPatchRequest, db: Session = Depends(get_db), user=Depends(require_user)):
    reminder = reminder_service.patch_reminder(db, reminder_id, body.model_dump(exclude_unset=True), user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.delete("/reminders/{reminder_id}", response_model=DeleteReminderResponse)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    reminder = reminder_service.delete_reminder(db, reminder_id, user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "deleted"}
