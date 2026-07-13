from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core import crypto
from app.core.config import settings
from app.db.models import GmailAccount
from app.services.auth_service import ALGORITHM, SECRET_KEY

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
STATE_EXPIRE_MINUTES = 10
TOKEN_REFRESH_SKEW_SECONDS = 60
OAUTH_STATE_COOKIE = "gmail_oauth_nonce"


class GmailOAuthError(Exception):
    pass


@dataclass(frozen=True)
class GmailOAuthState:
    user_id: int
    redirect_uri: str


def _require_oauth_config() -> None:
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise GmailOAuthError("Gmail OAuth is not configured")


def is_oauth_configured() -> bool:
    return bool(settings.gmail_client_id and settings.gmail_client_secret)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _from_db_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def create_oauth_nonce() -> str:
    return secrets.token_urlsafe(32)


def _fallback_redirect_uri() -> str:
    return settings.gmail_redirect_uri or "http://localhost:8000/api/gmail/oauth/callback"


def create_oauth_state(user_id: int, nonce: str, redirect_uri: str | None = None) -> str:
    expire = _utcnow() + timedelta(minutes=STATE_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "nonce": nonce,
        "redirect_uri": redirect_uri or _fallback_redirect_uri(),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def parse_oauth_state(state: str, expected_nonce: str) -> GmailOAuthState:
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        nonce = payload.get("nonce")
        if not user_id or not nonce or nonce != expected_nonce:
            raise GmailOAuthError("Invalid OAuth state")
        redirect_uri = payload.get("redirect_uri") or _fallback_redirect_uri()
        if not isinstance(redirect_uri, str):
            raise GmailOAuthError("Invalid OAuth state")
        return GmailOAuthState(user_id=int(user_id), redirect_uri=redirect_uri)
    except (JWTError, ValueError) as exc:
        raise GmailOAuthError("Invalid OAuth state") from exc


def build_authorization_url(user_id: int, nonce: str, redirect_uri: str | None = None) -> str:
    _require_oauth_config()
    redirect_uri = redirect_uri or _fallback_redirect_uri()
    params = {
        "client_id": settings.gmail_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": settings.gmail_scopes,
        "state": create_oauth_state(user_id, nonce, redirect_uri),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _post_token_request(data: dict[str, str]) -> dict[str, Any]:
    try:
        response = httpx.post(GOOGLE_TOKEN_URL, data=data, timeout=15, trust_env=True)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ImportError) as exc:
        logger.warning("Gmail OAuth token request failed: %s", exc)
        raise GmailOAuthError("Gmail OAuth token request failed") from exc


def _fetch_google_email(access_token: str) -> str | None:
    try:
        response = httpx.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
            trust_env=True,
        )
        response.raise_for_status()
        email = response.json().get("email")
        return email if isinstance(email, str) else None
    except (httpx.HTTPError, ImportError):
        logger.warning("Failed to fetch Gmail account email after OAuth callback.")
        return None


def _expires_at_from_token(token_data: dict[str, Any]) -> datetime | None:
    expires_in = token_data.get("expires_in")
    if expires_in is None:
        return None
    return _to_naive_utc(_utcnow() + timedelta(seconds=int(expires_in)))


def save_token_response(db: Session, user_id: int, token_data: dict[str, Any]) -> GmailAccount:
    access_token = token_data.get("access_token")
    if not access_token:
        raise GmailOAuthError("Gmail OAuth response did not include an access token")

    row = db.query(GmailAccount).filter(GmailAccount.user_id == user_id).first()
    existing_refresh_token = crypto.decrypt(row.refresh_token) if row and row.refresh_token else ""
    refresh_token = token_data.get("refresh_token") or existing_refresh_token
    email = _fetch_google_email(access_token) if "openid" in settings.gmail_scopes.split() else None

    values = {
        "email": email or (row.email if row else None),
        "access_token": crypto.encrypt(access_token),
        "refresh_token": crypto.encrypt(refresh_token) if refresh_token else None,
        "token_type": token_data.get("token_type", "Bearer"),
        "scopes": token_data.get("scope", settings.gmail_scopes),
        "expires_at": _expires_at_from_token(token_data),
    }

    if row:
        for key, value in values.items():
            setattr(row, key, value)
    else:
        row = GmailAccount(user_id=user_id, **values)
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


def exchange_code_for_tokens(db: Session, code: str, state: str, expected_nonce: str) -> GmailAccount:
    _require_oauth_config()
    oauth_state = parse_oauth_state(state, expected_nonce)
    token_data = _post_token_request(
        {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": oauth_state.redirect_uri,
        }
    )
    return save_token_response(db, oauth_state.user_id, token_data)


def get_gmail_account(db: Session, user_id: int) -> GmailAccount | None:
    return db.query(GmailAccount).filter(GmailAccount.user_id == user_id).first()


def get_gmail_status(db: Session, user_id: int) -> dict[str, Any]:
    row = get_gmail_account(db, user_id)
    if row is None:
        return {"connected": False, "configured": is_oauth_configured()}
    return {
        "connected": True,
        "configured": is_oauth_configured(),
        "email": row.email,
        "scopes": row.scopes,
        "expires_at": row.expires_at,
    }


def refresh_access_token(db: Session, user_id: int, force: bool = False) -> GmailAccount:
    _require_oauth_config()
    row = get_gmail_account(db, user_id)
    if row is None or not row.refresh_token:
        raise GmailOAuthError("Gmail account is not connected")

    expires_at = _from_db_datetime(row.expires_at)
    if not force and expires_at and expires_at > _utcnow() + timedelta(seconds=TOKEN_REFRESH_SKEW_SECONDS):
        return row

    refresh_token = crypto.decrypt(row.refresh_token)
    if not refresh_token:
        raise GmailOAuthError("Stored Gmail refresh token could not be decrypted")

    token_data = _post_token_request(
        {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    )
    return save_token_response(db, user_id, token_data)


def get_valid_access_token(db: Session, user_id: int) -> str:
    row = refresh_access_token(db, user_id)
    token = crypto.decrypt(row.access_token)
    if not token:
        raise GmailOAuthError("Stored Gmail access token could not be decrypted")
    return token


def disconnect_gmail(db: Session, user_id: int) -> None:
    row = get_gmail_account(db, user_id)
    if row is None:
        return
    db.delete(row)
    db.commit()
