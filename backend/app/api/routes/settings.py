from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.settings import AIProviderConfig
from app.services import settings_service, ai_service

router = APIRouter()


@router.get("/settings/ai", response_model=AIProviderConfig)
def get_ai_settings(db: Session = Depends(get_db)):
    return settings_service.get_ai_config(db)


@router.put("/settings/ai", response_model=AIProviderConfig)
def update_ai_settings(body: AIProviderConfig, db: Session = Depends(get_db)):
    result = settings_service.save_ai_config(db, body.model_dump())
    ai_service.reset_ai_provider()
    return result
