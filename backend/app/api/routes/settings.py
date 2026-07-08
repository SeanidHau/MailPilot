from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.schemas.settings import AIProviderConfig
from app.services import settings_service, ai_service
from app.api.deps import get_current_user, require_user

router = APIRouter()


@router.get("/settings/ai", response_model=AIProviderConfig)
def get_ai_settings(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    return settings_service.get_ai_config(db, user.id if user else None)


@router.put("/settings/ai", response_model=AIProviderConfig)
def update_ai_settings(
    body: AIProviderConfig,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    result = settings_service.save_ai_config(db, body.model_dump(), user.id)
    ai_service.reset_ai_provider()
    return result
