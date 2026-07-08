from __future__ import annotations

import secrets
import logging
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.db.models import User
from app.core.config import settings

logger = logging.getLogger(__name__)

SECRET_KEY = settings.jwt_secret_key
if SECRET_KEY == "change-me-in-production":
    SECRET_KEY = secrets.token_hex(32)
    logger.warning(
        "JWT_SECRET_KEY is still the default placeholder. "
        "A random temporary key has been generated for this session. "
        "Set JWT_SECRET_KEY in .env for production."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except JWTError:
        return None


def register_user(db: Session, email: str, password: str) -> User | None:
    if db.query(User).filter(User.email == email).first():
        return None
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
