import json
import pytest
from app.core import crypto


# ---- Fernet primitives ----

def test_encrypt_roundtrip():
    plain = "sk-proj-this-is-a-secret-api-key-12345"
    enc = crypto.encrypt(plain)
    assert enc != plain
    assert len(enc) > len(plain)
    assert crypto.decrypt(enc) == plain


def test_encrypt_empty_string():
    assert crypto.encrypt("") == ""
    assert crypto.decrypt("") == ""


def test_encrypt_different_inputs_produce_different_outputs():
    a = crypto.encrypt("key-alpha")
    b = crypto.encrypt("key-beta")
    assert a != b


def test_encrypt_same_input_different_ciphertext():
    """Fernet uses random IV, so encrypting the same plaintext twice yields different tokens."""
    enc1 = crypto.encrypt("same-key")
    enc2 = crypto.encrypt("same-key")
    assert enc1 != enc2
    # Both should decrypt to the same value
    assert crypto.decrypt(enc1) == "same-key"
    assert crypto.decrypt(enc2) == "same-key"


def test_decrypt_invalid_token_returns_empty():
    assert crypto.decrypt("garbage") == ""
    assert crypto.decrypt("gAAAAABinvalid123") == ""


def test_decrypt_truncated_token_returns_empty():
    valid = crypto.encrypt("secret")
    truncated = valid[:20]
    assert crypto.decrypt(truncated) == ""


def test_decrypt_tampered_token_returns_empty():
    """HMAC verification should detect tampering."""
    valid = crypto.encrypt("secret")
    # Flip a character in the middle
    idx = len(valid) // 2
    tampered = valid[:idx] + ('A' if valid[idx] != 'A' else 'B') + valid[idx + 1:]
    assert crypto.decrypt(tampered) == ""


# ---- API-level encryption tests ----

def test_api_key_stored_encrypted(auth_client, db_session):
    """Save an AI config and verify the stored API key is encrypted (not plaintext)."""
    resp = auth_client.put(
        "/api/settings/ai",
        json={"provider": "openai", "openai_api_key": "sk-secret-key-12345", "openai_model": "gpt-4o"},
    )
    assert resp.status_code == 200

    from app.db.models import Setting
    row = db_session.query(Setting).filter(Setting.key.like("%ai_config")).first()

    assert row is not None
    stored = json.loads(row.value)
    stored_key = stored.get("openai_api_key", "")
    # Must NOT be the plaintext key
    assert stored_key != "sk-secret-key-12345"
    # Must be a Fernet token (starts with gAAAAAB)
    assert stored_key.startswith("gAAAAAB")
    # Must be longer than plaintext (Fernet adds overhead)
    assert len(stored_key) > len("sk-secret-key-12345")


def test_api_key_returned_decrypted(auth_client):
    """API response must return the decrypted key, not the stored ciphertext."""
    auth_client.put(
        "/api/settings/ai",
        json={"provider": "openai", "openai_api_key": "sk-my-key", "openai_model": "gpt-4o"},
    )
    resp = auth_client.get("/api/settings/ai")
    assert resp.status_code == 200
    assert resp.json()["openai_api_key"] == "sk-my-key"


def test_empty_api_key_not_encrypted(auth_client):
    """Empty API keys should pass through without encryption."""
    auth_client.put(
        "/api/settings/ai",
        json={"provider": "mock", "openai_api_key": "", "anthropic_api_key": ""},
    )
    resp = auth_client.get("/api/settings/ai")
    assert resp.status_code == 200
    assert resp.json()["openai_api_key"] == ""
    assert resp.json()["anthropic_api_key"] == ""


def test_save_and_retrieve_multiple_keys(auth_client, db_session):
    """Both OpenAI and Anthropic keys should be independently encrypted/decrypted."""
    auth_client.put(
        "/api/settings/ai",
        json={
            "provider": "anthropic",
            "openai_api_key": "sk-openai-abc",
            "anthropic_api_key": "sk-ant-xyz",
            "openai_model": "gpt-4o",
            "anthropic_model": "claude-sonnet-4-5",
        },
    )
    resp = auth_client.get("/api/settings/ai")
    assert resp.status_code == 200
    data = resp.json()
    assert data["openai_api_key"] == "sk-openai-abc"
    assert data["anthropic_api_key"] == "sk-ant-xyz"
    assert data["provider"] == "anthropic"

    # Verify both keys are encrypted at rest
    from app.db.models import Setting
    row = db_session.query(Setting).filter(Setting.key.like("%ai_config")).first()
    stored = json.loads(row.value)
    assert stored["openai_api_key"].startswith("gAAAAAB")
    assert stored["anthropic_api_key"].startswith("gAAAAAB")


def test_partial_key_update_does_not_clear_other_keys(auth_client):
    """Updating only OpenAI key should not affect the stored Anthropic key."""
    auth_client.put(
        "/api/settings/ai",
        json={
            "provider": "openai",
            "openai_api_key": "sk-openai-first",
            "anthropic_api_key": "sk-ant-persist",
        },
    )
    # Update only the OpenAI key
    auth_client.put(
        "/api/settings/ai",
        json={"provider": "openai", "openai_api_key": "sk-openai-second"},
    )
    resp = auth_client.get("/api/settings/ai")
    assert resp.status_code == 200
    data = resp.json()
    assert data["openai_api_key"] == "sk-openai-second"
    assert data["anthropic_api_key"] == "sk-ant-persist"


def test_encryption_per_user_isolation(auth_client, client):
    """Different users' keys are encrypted independently."""
    # User A saves a key
    auth_client.put(
        "/api/settings/ai",
        json={"provider": "openai", "openai_api_key": "sk-user-a-key"},
    )

    # Register User B
    r = client.post("/api/auth/register", json={"email": "encb@test.dev", "password": "123456"})
    token_b = r.json()["access_token"]

    # Use a separate header dict to not pollute auth_client
    headers_b = {"Authorization": f"Bearer {token_b}"}
    client.put(
        "/api/settings/ai",
        json={"provider": "openai", "openai_api_key": "sk-user-b-key"},
        headers=headers_b,
    )

    # User A sees their own key
    resp_a = auth_client.get("/api/settings/ai")
    assert resp_a.json()["openai_api_key"] == "sk-user-a-key"

    # User B sees their key (using per-request header)
    resp_b = client.get("/api/settings/ai", headers=headers_b)
    assert resp_b.json()["openai_api_key"] == "sk-user-b-key"
