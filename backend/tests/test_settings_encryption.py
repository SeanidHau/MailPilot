import json
from datetime import datetime

from cryptography.fernet import Fernet

from app.core import crypto
from app.core.config import settings
from app.db.models import Setting
from app.services.settings_service import AI_SETTINGS_KEY


def test_ai_api_key_is_encrypted_at_rest_and_decrypts_with_stable_key(
    auth_client,
    db_session,
    monkeypatch,
):
    stable_key = Fernet.generate_key().decode()
    openai_api_key = "sk-test-secret-key"

    monkeypatch.setattr(settings, "encryption_key", stable_key)
    monkeypatch.setattr(crypto, "_fernet", None)

    resp = auth_client.put(
        "/api/settings/ai",
        json={
            "provider": "openai",
            "openai_api_key": openai_api_key,
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o-mini",
            "anthropic_api_key": "",
            "anthropic_base_url": "https://api.anthropic.com",
            "anthropic_model": "claude-sonnet-4-5-20250929",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["openai_api_key"] == openai_api_key

    user_id = auth_client.get("/api/auth/me").json()["id"]
    row = db_session.query(Setting).filter(Setting.key == f"u{user_id}:{AI_SETTINGS_KEY}").one()
    stored = json.loads(row.value)

    assert stored["openai_api_key"] != openai_api_key
    assert openai_api_key not in row.value

    monkeypatch.setattr(crypto, "_fernet", None)
    resp = auth_client.get("/api/settings/ai")

    assert resp.status_code == 200
    assert resp.json()["openai_api_key"] == openai_api_key


def test_saving_ai_settings_processes_existing_unprocessed_email(auth_client, db_session):
    from app.db.models import Email

    user_id = auth_client.get("/api/auth/me").json()["id"]
    email = Email(
        message_id="settings-processing-001",
        sender="alice@example.com",
        recipients="me@example.com",
        subject="Action Required: review the deadline",
        body="Please review this deadline and reply by 2026-07-20.",
        received_at=datetime(2026, 7, 10, 10, 0),
        user_id=user_id,
    )
    db_session.add(email)
    db_session.commit()

    response = auth_client.put(
        "/api/settings/ai",
        json={
            "provider": "mock",
            "openai_api_key": "",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
            "anthropic_api_key": "",
            "anthropic_base_url": "https://api.anthropic.com",
            "anthropic_model": "claude-sonnet-4-5-20250929",
        },
    )

    assert response.status_code == 200
    db_session.refresh(email)
    assert email.summary
    assert email.ai_metadata is not None
