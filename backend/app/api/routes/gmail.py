from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import require_user
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.gmail import (
    GmailAuthorizeResponse,
    GmailRefreshResponse,
    GmailStatusResponse,
)
from app.services import gmail_service
from app.services.gmail_service import GmailOAuthError

router = APIRouter()


def _oauth_error(exc: GmailOAuthError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/gmail/authorize", response_model=GmailAuthorizeResponse)
def authorize_gmail(user: User = Depends(require_user)):
    try:
        return {"authorization_url": gmail_service.build_authorization_url(user.id)}
    except GmailOAuthError as exc:
        raise _oauth_error(exc)


@router.get("/gmail/oauth/callback")
def gmail_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        gmail_service.exchange_code_for_tokens(db, code, state)
        return RedirectResponse(settings.gmail_oauth_success_url)
    except GmailOAuthError:
        return RedirectResponse(settings.gmail_oauth_failure_url)


@router.get("/gmail/status", response_model=GmailStatusResponse)
def gmail_status(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return gmail_service.get_gmail_status(db, user.id)


@router.post("/gmail/refresh", response_model=GmailRefreshResponse)
def refresh_gmail_token(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        row = gmail_service.refresh_access_token(db, user.id, force=True)
        return {"connected": True, "expires_at": row.expires_at}
    except GmailOAuthError as exc:
        raise _oauth_error(exc)


@router.delete("/gmail/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_gmail(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    gmail_service.disconnect_gmail(db, user.id)
