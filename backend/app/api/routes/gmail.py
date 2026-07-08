from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
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
def authorize_gmail(response: Response, user: User = Depends(require_user)):
    try:
        nonce = gmail_service.create_oauth_nonce()
        response.set_cookie(
            gmail_service.OAUTH_STATE_COOKIE,
            nonce,
            httponly=True,
            secure=settings.gmail_redirect_uri.startswith("https://"),
            samesite="lax",
            max_age=gmail_service.STATE_EXPIRE_MINUTES * 60,
            path="/api/gmail/oauth/callback",
        )
        return {"authorization_url": gmail_service.build_authorization_url(user.id, nonce)}
    except GmailOAuthError as exc:
        raise _oauth_error(exc)


@router.get("/gmail/oauth/callback")
def gmail_oauth_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    def redirect_failure():
        response = RedirectResponse(settings.gmail_oauth_failure_url)
        response.delete_cookie(gmail_service.OAUTH_STATE_COOKIE, path="/api/gmail/oauth/callback")
        return response

    if error or not code or not state:
        return redirect_failure()

    nonce = request.cookies.get(gmail_service.OAUTH_STATE_COOKIE)
    if not nonce:
        return redirect_failure()

    try:
        gmail_service.exchange_code_for_tokens(db, code, state, nonce)
        response = RedirectResponse(settings.gmail_oauth_success_url)
        response.delete_cookie(gmail_service.OAUTH_STATE_COOKIE, path="/api/gmail/oauth/callback")
        return response
    except GmailOAuthError:
        return redirect_failure()


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
