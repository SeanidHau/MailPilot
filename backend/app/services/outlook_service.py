"""Outlook / Microsoft Graph OAuth service (mirrors Gmail OAuth pattern)."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core import crypto
from app.core.config import settings
from app.db.models import OutlookAccount
from app.services.auth_service import ALGORITHM, SECRET_KEY

logger = logging.getLogger(__name__)

MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MS_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"

STATE_EXPIRE_MINUTES = 10
TOKEN_REFRESH_SKEW_SECONDS = 60
OAUTH_STATE_COOKIE = "outlook_oauth_nonce"


class OutlookOAuthError(Exception):
    pass


def _require_oauth_config() -> None:
    if not settings.outlook_client_id or not settings.outlook_client_secret:
        raise OutlookOAuthError("Outlook OAuth is not configured")


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


def create_oauth_state(user_id: int, nonce: str) -> str:
    expire = _utcnow() + timedelta(minutes=STATE_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "nonce": nonce, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def parse_oauth_state(state: str, expected_nonce: str) -> int:
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        nonce = payload.get("nonce")
        if not user_id or not nonce or nonce != expected_nonce:
            raise OutlookOAuthError("Invalid OAuth state")
        return int(user_id)
    except (JWTError, ValueError) as exc:
        raise OutlookOAuthError("Invalid OAuth state") from exc

def build_authorization_url(user_id: int, nonce: str) -> str:
    _require_oauth_config()
    state = create_oauth_state(user_id, nonce)
    params = {
        "client_id": settings.outlook_client_id,
        "response_type": "code",
        "redirect_uri": settings.outlook_redirect_uri,
        "scope": settings.outlook_scopes,
        "state": state,
        "response_mode": "query",
    }
    return f"{MS_AUTH_URL}?{urlencode(params)}"

def exchange_code_for_tokens(db: Session, code: str, state: str, expected_nonce: str) -> OutlookAccount:
    _require_oauth_config()
    user_id = parse_oauth_state(state, expected_nonce)
    token_data = _post_token_request({
        "client_id": settings.outlook_client_id,
        "client_secret": settings.outlook_client_secret,
        "code": code,
        "redirect_uri": settings.outlook_redirect_uri,
        "grant_type": "authorization_code",
    })
    return save_token_response(db, user_id, token_data)


def save_token_response(db: Session, user_id: int, token_data: dict[str, Any]) -> OutlookAccount:
    access_token = token_data.get("access_token")
    if not access_token:
        raise OutlookOAuthError("Outlook OAuth response did not include an access token")

    row = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()
    existing_refresh = crypto.decrypt(row.refresh_token) if row and row.refresh_token else ""

    refresh_token = token_data.get("refresh_token") or existing_refresh
    email = _fetch_ms_email(access_token)

    if row:
        row.access_token = crypto.encrypt(access_token)
        row.refresh_token = crypto.encrypt(refresh_token) if refresh_token else None
        row.token_type = token_data.get("token_type", "Bearer")
        row.scopes = token_data.get("scope", settings.outlook_scopes)
        row.expires_at = _expires_at_from_token(token_data)
        if email:
            row.email = email
    else:
        row = OutlookAccount(
            user_id=user_id,
            email=email,
            access_token=crypto.encrypt(access_token),
            refresh_token=crypto.encrypt(refresh_token) if refresh_token else None,
            token_type=token_data.get("token_type", "Bearer"),
            scopes=token_data.get("scope", settings.outlook_scopes),
            expires_at=_expires_at_from_token(token_data),
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


def refresh_access_token(db: Session, user_id: int, force: bool = False) -> OutlookAccount:
    _require_oauth_config()
    row = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()
    if not row:
        raise OutlookOAuthError("Outlook account not connected")

    expires_at = _from_db_datetime(row.expires_at)
    if not force and expires_at and expires_at > _utcnow() + timedelta(seconds=TOKEN_REFRESH_SKEW_SECONDS):
        return row

    if not row.refresh_token:
        raise OutlookOAuthError("No refresh token available")

    refresh_token = crypto.decrypt(row.refresh_token)
    if not refresh_token:
        raise OutlookOAuthError("Failed to decrypt refresh token")

    token_data = _post_token_request({
        "client_id": settings.outlook_client_id,
        "client_secret": settings.outlook_client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    })
    return save_token_response(db, user_id, token_data)


def get_valid_access_token(db: Session, user_id: int) -> str:
    row = refresh_access_token(db, user_id)
    token = crypto.decrypt(row.access_token)
    if not token:
        raise OutlookOAuthError("Stored Outlook access token could not be decrypted")
    return token

def get_outlook_status(db: Session, user_id: int) -> dict[str, Any]:
    row = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()
    if not row:
        return {"connected": False}
    return {
        "connected": True,
        "email": row.email,
        "scopes": row.scopes,
        "expires_at": row.expires_at,
    }


def disconnect_outlook(db: Session, user_id: int) -> None:
    row = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()
    if row:
        db.delete(row)
        db.commit()


# -- helpers --

def _post_token_request(data: dict[str, str]) -> dict[str, Any]:
    try:
        resp = httpx.post(MS_TOKEN_URL, data=data, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        logger.warning("Outlook OAuth token request failed: %s", exc)
        raise OutlookOAuthError("Outlook OAuth token request failed") from exc


def _fetch_ms_email(access_token: str) -> str | None:
    try:
        resp = httpx.get(
            MS_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("mail") or data.get("userPrincipalName")
    except Exception:
        return None


def _expires_at_from_token(token_data: dict[str, Any]) -> datetime | None:
    expires_in = token_data.get("expires_in")
    if isinstance(expires_in, (int, float)) and expires_in > 0:
        return _to_naive_utc(_utcnow() + timedelta(seconds=int(expires_in)))
    return None
