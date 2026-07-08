from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services import auth_service
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要 6 个字符")
    user = auth_service.register_user(db, body.email.strip().lower(), body.password)
    if not user:
        raise HTTPException(status_code=409, detail="该邮箱已被注册")
    token = auth_service.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, body.email.strip().lower(), body.password)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = auth_service.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
def get_me(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return {"id": user.id, "email": user.email}
