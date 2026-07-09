import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from cryptography.fernet import Fernet

from app.core import crypto
from app.core.config import settings
from app.db.models import OutlookAccount
from app.services import outlook_service


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


def setup_outlook_config(monkeypatch):
    monkeypatch.setattr(settings, "outlook_client_id", "outlook-client-id")
    monkeypatch.setattr(settings, "outlook_client_secret", "outlook-client-secret")
    monkeypatch.setattr(settings, "outlook_redirect_uri", "http://testserver/api/outlook/oauth/callback")
    monkeypatch.setattr(settings, "outlook_scopes", "offline_access User.Read Mail.Read")
    monkeypatch.setattr(settings, "encryption_key", Fernet.generate_key().decode())
    monkeypatch.setattr(crypto, "_fernet", None)


def test_build_authorization_url_includes_graph_scopes_and_signed_state(monkeypatch):
    setup_outlook_config(monkeypatch)
    nonce = outlook_service.create_oauth_nonce()

    auth_url = outlook_service.build_authorization_url(user_id=123, nonce=nonce)
    params = parse_qs(urlparse(auth_url).query)

    assert params["client_id"] == ["outlook-client-id"]
    assert params["redirect_uri"] == ["http://testserver/api/outlook/oauth/callback"]
    assert params["response_type"] == ["code"]
    assert params["response_mode"] == ["query"]
    assert "offline_access" in params["scope"][0]
    assert "Mail.Read" in params["scope"][0]
    assert outlook_service.parse_oauth_state(params["state"][0], nonce) == 123


def test_authorize_sets_http_only_nonce_cookie(auth_client, monkeypatch):
    setup_outlook_config(monkeypatch)

    resp = auth_client.get("/api/outlook/authorize")
    params = parse_qs(urlparse(resp.json()["authorization_url"]).query)

    assert resp.status_code == 200
    assert outlook_service.OAUTH_STATE_COOKIE in resp.cookies
    assert "httponly" in resp.headers["set-cookie"].lower()
    assert outlook_service.parse_oauth_state(params["state"][0], resp.cookies[outlook_service.OAUTH_STATE_COOKIE])


def test_authorize_requires_oauth_config(auth_client, monkeypatch):
    monkeypatch.setattr(settings, "outlook_client_id", "")
    monkeypatch.setattr(settings, "outlook_client_secret", "")

    resp = auth_client.get("/api/outlook/authorize")

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Outlook OAuth is not configured"


def test_exchange_code_encrypts_tokens_and_stores_account(db_session, monkeypatch):
    setup_outlook_config(monkeypatch)
    nonce = outlook_service.create_oauth_nonce()
    state = outlook_service.create_oauth_state(user_id=7, nonce=nonce)

    def fake_post(url, data, timeout):
        assert url == outlook_service.MS_TOKEN_URL
        assert data["grant_type"] == "authorization_code"
        assert data["code"] == "auth-code"
        return FakeResponse(
            {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": settings.outlook_scopes,
            }
        )

    def fake_get(url, headers, timeout):
        assert url == outlook_service.MS_USERINFO_URL
        assert headers["Authorization"] == "Bearer access-token"
        return FakeResponse({"mail": "user@outlook.com"})

    monkeypatch.setattr(outlook_service.httpx, "post", fake_post)
    monkeypatch.setattr(outlook_service.httpx, "get", fake_get)

    row = outlook_service.exchange_code_for_tokens(db_session, "auth-code", state, nonce)
    stored = db_session.query(OutlookAccount).filter(OutlookAccount.user_id == 7).one()

    assert row.email == "user@outlook.com"
    assert stored.access_token != "access-token"
    assert stored.refresh_token != "refresh-token"
    assert "access-token" not in json.dumps({"access_token": stored.access_token})
    assert crypto.decrypt(stored.access_token) == "access-token"
    assert crypto.decrypt(stored.refresh_token) == "refresh-token"


def test_exchange_code_rejects_state_without_matching_cookie_nonce(db_session, monkeypatch):
    setup_outlook_config(monkeypatch)
    state = outlook_service.create_oauth_state(user_id=7, nonce="attacker-nonce")

    try:
        outlook_service.exchange_code_for_tokens(db_session, "auth-code", state, "victim-cookie-nonce")
    except outlook_service.OutlookOAuthError as exc:
        assert "Invalid OAuth state" in str(exc)
    else:
        raise AssertionError("Expected mismatched OAuth nonce to be rejected")

    assert db_session.query(OutlookAccount).filter(OutlookAccount.user_id == 7).first() is None


def test_callback_redirects_to_failure_when_microsoft_denies_access(auth_client, monkeypatch):
    setup_outlook_config(monkeypatch)
    monkeypatch.setattr(settings, "outlook_oauth_failure_url", "http://frontend/settings?outlook=error")

    resp = auth_client.get(
        "/api/outlook/oauth/callback?error=access_denied&state=ignored",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "http://frontend/settings?outlook=error"


def test_callback_redirects_to_failure_without_nonce_cookie(client, monkeypatch):
    setup_outlook_config(monkeypatch)
    monkeypatch.setattr(settings, "outlook_oauth_failure_url", "http://frontend/settings?outlook=error")
    state = outlook_service.create_oauth_state(user_id=1, nonce="nonce")

    resp = client.get(
        f"/api/outlook/oauth/callback?code=auth-code&state={state}",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "http://frontend/settings?outlook=error"


def test_refresh_access_token_reuses_stored_refresh_token(db_session, monkeypatch):
    setup_outlook_config(monkeypatch)
    db_session.add(
        OutlookAccount(
            user_id=3,
            email="user@outlook.com",
            access_token=crypto.encrypt("old-access-token"),
            refresh_token=crypto.encrypt("stable-refresh-token"),
            token_type="Bearer",
            scopes=settings.outlook_scopes,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1),
        )
    )
    db_session.commit()

    def fake_post(url, data, timeout):
        assert url == outlook_service.MS_TOKEN_URL
        assert data["grant_type"] == "refresh_token"
        assert data["refresh_token"] == "stable-refresh-token"
        return FakeResponse(
            {
                "access_token": "new-access-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": settings.outlook_scopes,
            }
        )

    monkeypatch.setattr(outlook_service.httpx, "post", fake_post)
    monkeypatch.setattr(outlook_service.httpx, "get", lambda *args, **kwargs: FakeResponse({"mail": "user@outlook.com"}))

    row = outlook_service.refresh_access_token(db_session, user_id=3, force=True)

    assert crypto.decrypt(row.access_token) == "new-access-token"
    assert crypto.decrypt(row.refresh_token) == "stable-refresh-token"
    assert outlook_service.get_valid_access_token(db_session, user_id=3) == "new-access-token"
