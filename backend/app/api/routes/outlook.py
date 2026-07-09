from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User
from app.schemas.outlook import OutlookAuthorizeResponse, OutlookStatusResponse
from app.services import outlook_service
from app.api.deps import require_user

router = APIRouter()


@router.get("/outlook/authorize", response_model=OutlookAuthorizeResponse)
def authorize_outlook(response: Response, user: User = Depends(require_user)):
    nonce = outlook_service.create_oauth_nonce()
    response.set_cookie(
        outlook_service.OAUTH_STATE_COOKIE,
        nonce,
        httponly=True,
        secure=settings.outlook_redirect_uri.startswith("https://"),
        samesite="lax",
        max_age=outlook_service.STATE_EXPIRE_MINUTES * 60,
        path="/api/outlook/oauth/callback",
    )
    return {"authorization_url": outlook_service.build_authorization_url(user.id, nonce)}


@router.get("/outlook/oauth/callback")
def outlook_oauth_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    if error:
        return RedirectResponse(settings.outlook_oauth_failure_url)
    if not code or not state:
        return RedirectResponse(settings.outlook_oauth_failure_url)
    nonce = request.cookies.get(outlook_service.OAUTH_STATE_COOKIE, "")
    try:
        outlook_service.exchange_code_for_tokens(db, code, state, nonce)
        redirect_url = settings.outlook_oauth_success_url
    except outlook_service.OutlookOAuthError:
        redirect_url = settings.outlook_oauth_failure_url

    resp = RedirectResponse(redirect_url)
    resp.delete_cookie(outlook_service.OAUTH_STATE_COOKIE, path="/api/outlook/oauth/callback")
    return resp


@router.get("/outlook/status", response_model=OutlookStatusResponse)
def outlook_status(db: Session = Depends(get_db), user: User = Depends(require_user)):
    return outlook_service.get_outlook_status(db, user.id)


@router.post("/outlook/refresh", response_model=OutlookStatusResponse)
def refresh_outlook_token(db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        row = outlook_service.refresh_access_token(db, user.id, force=True)
        return {"connected": True, "email": row.email, "scopes": row.scopes, "expires_at": row.expires_at}
    except outlook_service.OutlookOAuthError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/outlook/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_outlook(db: Session = Depends(get_db), user: User = Depends(require_user)):
    outlook_service.disconnect_outlook(db, user.id)
