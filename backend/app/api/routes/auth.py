from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/auth/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if len(body.password) < 6:
        logger.info("auth_failure", extra={"reason": "short_password", "email": email})
        raise HTTPException(status_code=400, detail="\u5bc6\u7801\u81f3\u5c11\u9700\u8981 6 \u4e2a\u5b57\u7b26")

    user = auth_service.register_user(db, email, body.password)
    if not user:
        logger.info("auth_failure", extra={"reason": "duplicate_registration", "email": email})
        raise HTTPException(status_code=409, detail="\u8be5\u90ae\u7bb1\u5df2\u88ab\u6ce8\u518c")

    token = auth_service.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = auth_service.authenticate_user(db, email, body.password)
    if not user:
        logger.info("auth_failure", extra={"reason": "invalid_credentials", "email": email})
        raise HTTPException(status_code=401, detail="\u90ae\u7bb1\u6216\u5bc6\u7801\u9519\u8bef")

    token = auth_service.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
def get_me(user=Depends(get_current_user)):
    if not user:
        logger.info("auth_failure", extra={"reason": "missing_or_invalid_token"})
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"id": user.id, "email": user.email}
