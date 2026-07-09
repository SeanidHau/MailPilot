"""Outlook / Microsoft Graph OAuth service (mirrors Gmail OAuth pattern)."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from jose import jwt
from sqlalchemy.orm import Session

from app.core import crypto
from app.core.config import settings
from app.db.models import OutlookAccount
from app.services.auth_service import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)

MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MS_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"

STATE_EXPIRE_MINUTES = 10
TOKEN_REFRESH_SKEW_SECONDS = 60
OAUTH_STATE_COOKIE = "outlook_oauth_nonce"


class OutlookOAuthError(Exception):
    pass


# -- nonce / state (CSRF protection) --

def create_oauth_nonce() -> str:
    return secrets.token_urlsafe(32)


def create_oauth_state(user_id: int, nonce: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=STATE_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "nonce": nonce, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def parse_oauth_state(state: str, expected_nonce: str) -> int:
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise OutlookOAuthError("Invalid OAuth state")
    if payload.get("nonce") != expected_nonce:
        raise OutlookOAuthError("OAuth state nonce mismatch")
    user_id = payload.get("sub")
    if user_id is None:
        raise OutlookOAuthError("OAuth state missing user_id")
    return int(user_id)


# -- authorization URL --

def build_authorization_url(user_id: int, nonce: str) -> str:
    state = create_oauth_state(user_id, nonce)
    params = {
        "client_id": settings.outlook_client_id,
        "response_type": "code",
        "redirect_uri": settings.outlook_redirect_uri,
        "scope": settings.outlook_scopes,
        "state": state,
        "response_mode": "query",
    }
    query = "&".join(f"{k}={httpx.URL('')._encode_param(v)}" for k, v in params.items())
    return f"{MS_AUTH_URL}?{query}"


# -- token exchange --

def exchange_code_for_tokens(db: Session, code: str, state: str, expected_nonce: str) -> OutlookAccount:
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
    row = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()
    existing_refresh = crypto.decrypt(row.refresh_token) if row and row.refresh_token else None

    refresh_token = token_data.get("refresh_token") or existing_refresh
    email = _fetch_ms_email(token_data.get("access_token", ""))

    if row:
        row.access_token = crypto.encrypt(token_data["access_token"])
        row.refresh_token = crypto.encrypt(refresh_token) if refresh_token else None
        row.token_type = token_data.get("token_type", "Bearer")
        row.scopes = token_data.get("scope")
        row.expires_at = _expires_at_from_token(token_data)
        if email:
            row.email = email
    else:
        row = OutlookAccount(
            user_id=user_id,
            email=email,
            access_token=crypto.encrypt(token_data["access_token"]),
            refresh_token=crypto.encrypt(refresh_token) if refresh_token else None,
            token_type=token_data.get("token_type", "Bearer"),
            scopes=token_data.get("scope"),
            expires_at=_expires_at_from_token(token_data),
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


# -- token refresh --

def refresh_access_token(db: Session, user_id: int, force: bool = False) -> OutlookAccount:
    row = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()
    if not row:
        raise OutlookOAuthError("Outlook account not connected")

    if not force and row.expires_at:
        if row.expires_at > datetime.now(timezone.utc) + timedelta(seconds=TOKEN_REFRESH_SKEW_SECONDS):
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
    return crypto.decrypt(row.access_token)


# -- status / disconnect --

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
    except httpx.HTTPStatusError as exc:
        raise OutlookOAuthError(f"Token request failed: {exc.response.status_code} {exc.response.text}")
    except httpx.RequestError as exc:
        raise OutlookOAuthError(f"Token request error: {exc}")


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
        return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
    return None
