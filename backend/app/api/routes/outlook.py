from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User
from app.schemas.outlook import OutlookAuthorizeResponse, OutlookStatusResponse
from app.services import outlook_service
from app.api.deps import require_user

router = APIRouter()


def _oauth_error(exc: outlook_service.OutlookOAuthError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/outlook/authorize", response_model=OutlookAuthorizeResponse)
def authorize_outlook(response: Response, user: User = Depends(require_user)):
    try:
        nonce = outlook_service.create_oauth_nonce()
        authorization_url = outlook_service.build_authorization_url(user.id, nonce)
        response.set_cookie(
            outlook_service.OAUTH_STATE_COOKIE,
            nonce,
            httponly=True,
            secure=settings.outlook_redirect_uri.startswith("https://"),
            samesite="lax",
            max_age=outlook_service.STATE_EXPIRE_MINUTES * 60,
            path="/api/outlook/oauth/callback",
        )
        return {"authorization_url": authorization_url}
    except outlook_service.OutlookOAuthError as exc:
        raise _oauth_error(exc)


@router.get("/outlook/oauth/callback")
def outlook_oauth_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    def redirect_failure():
        response = RedirectResponse(settings.outlook_oauth_failure_url)
        response.delete_cookie(outlook_service.OAUTH_STATE_COOKIE, path="/api/outlook/oauth/callback")
        return response

    if error or not code or not state:
        return redirect_failure()

    nonce = request.cookies.get(outlook_service.OAUTH_STATE_COOKIE)
    if not nonce:
        return redirect_failure()

    try:
        outlook_service.exchange_code_for_tokens(db, code, state, nonce)
        response = RedirectResponse(settings.outlook_oauth_success_url)
        response.delete_cookie(outlook_service.OAUTH_STATE_COOKIE, path="/api/outlook/oauth/callback")
        return response
    except outlook_service.OutlookOAuthError:
        return redirect_failure()


@router.get("/outlook/status", response_model=OutlookStatusResponse)
def outlook_status(db: Session = Depends(get_db), user: User = Depends(require_user)):
    return outlook_service.get_outlook_status(db, user.id)


@router.post("/outlook/refresh", response_model=OutlookStatusResponse)
def refresh_outlook_token(db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        row = outlook_service.refresh_access_token(db, user.id, force=True)
        return {"connected": True, "email": row.email, "scopes": row.scopes, "expires_at": row.expires_at}
    except outlook_service.OutlookOAuthError as exc:
        raise _oauth_error(exc)


@router.delete("/outlook/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_outlook(db: Session = Depends(get_db), user: User = Depends(require_user)):
    outlook_service.disconnect_outlook(db, user.id)
