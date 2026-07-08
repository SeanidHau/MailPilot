from jose import jwt


# ---- Register ----

def test_register_returns_token(client):
    resp = client.post("/api/auth/register", json={"email": "new@test.dev", "password": "123456"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_register_rejects_short_password(client):
    resp = client.post("/api/auth/register", json={"email": "new@test.dev", "password": "12345"})
    assert resp.status_code == 400
    assert "密码" in resp.json()["detail"]


def test_register_rejects_duplicate_email(client):
    client.post("/api/auth/register", json={"email": "dup@test.dev", "password": "123456"})
    resp = client.post("/api/auth/register", json={"email": "dup@test.dev", "password": "123456"})
    assert resp.status_code == 409
    assert "注册" in resp.json()["detail"]


def test_register_persists_hashed_password(client, db_session):
    """Verify password is stored as bcrypt hash, not plaintext."""
    client.post("/api/auth/register", json={"email": "hash@test.dev", "password": "secret123"})
    from app.db.models import User
    user = db_session.query(User).filter(User.email == "hash@test.dev").first()
    assert user is not None
    assert user.hashed_password != "secret123"
    assert user.hashed_password.startswith("$2b$")


# ---- Login ----

def test_login_returns_token(client):
    client.post("/api/auth/register", json={"email": "login@test.dev", "password": "mypassword"})
    resp = client.post("/api/auth/login", json={"email": "login@test.dev", "password": "mypassword"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_rejects_wrong_password(client):
    client.post("/api/auth/register", json={"email": "wrong@test.dev", "password": "correct"})
    resp = client.post("/api/auth/login", json={"email": "wrong@test.dev", "password": "incorrect"})
    assert resp.status_code == 401
    assert "密码" in resp.json()["detail"]


def test_login_rejects_nonexistent_user(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@test.dev", "password": "anything"})
    assert resp.status_code == 401


def test_login_is_case_insensitive_for_email(client):
    client.post("/api/auth/register", json={"email": "Case@Test.dev", "password": "123456"})
    resp = client.post("/api/auth/login", json={"email": "case@test.dev", "password": "123456"})
    assert resp.status_code == 200


# ---- /auth/me ----

def test_me_returns_user(client):
    resp = client.post("/api/auth/register", json={"email": "me@test.dev", "password": "123456"})
    token = resp.json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["id"], int)
    assert data["email"] == "me@test.dev"


def test_me_rejects_no_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_rejects_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage.invalid.token"})
    assert resp.status_code == 401


def test_me_rejects_expired_token(client):
    """Generate an already-expired JWT and verify it's rejected."""
    from app.services.auth_service import SECRET_KEY, ALGORITHM
    from datetime import datetime, timedelta, timezone
    expire = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_token = jwt.encode({"sub": "1", "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_me_returns_different_users(client):
    """Register two users and verify each sees their own data."""
    r1 = client.post("/api/auth/register", json={"email": "user1@test.dev", "password": "123456"})
    token1 = r1.json()["access_token"]
    r2 = client.post("/api/auth/register", json={"email": "user2@test.dev", "password": "123456"})
    token2 = r2.json()["access_token"]

    me1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"}).json()
    me2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token2}"}).json()

    assert me1["email"] == "user1@test.dev"
    assert me2["email"] == "user2@test.dev"
    assert me1["id"] != me2["id"]


# ---- Token behavior ----

def test_token_across_requests(client):
    """Token obtained from login works on subsequent requests."""
    client.post("/api/auth/register", json={"email": "persist@test.dev", "password": "123456"})
    login_resp = client.post("/api/auth/login", json={"email": "persist@test.dev", "password": "123456"})
    token = login_resp.json()["access_token"]

    # Multiple requests with same token should all succeed
    for _ in range(3):
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "persist@test.dev"


def test_token_decodes_to_user_id(client):
    resp = client.post("/api/auth/register", json={"email": "tokenuser@test.dev", "password": "123456"})
    token = resp.json()["access_token"]

    from app.services.auth_service import decode_token
    user_id = decode_token(token)
    assert user_id is not None
    assert isinstance(user_id, int)


def test_data_isolation_between_users(client):
    """User A's emails are invisible to User B."""
    r1 = client.post("/api/auth/register", json={"email": "isoa@test.dev", "password": "123456"})
    t1 = r1.json()["access_token"]
    r2 = client.post("/api/auth/register", json={"email": "isob@test.dev", "password": "123456"})
    t2 = r2.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {t1}"
    client.post("/api/emails/import")

    # Switch to user B - should see 0 emails
    client.headers["Authorization"] = f"Bearer {t2}"
    resp = client.get("/api/emails")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # Cross-access A's email with B's token should return 404
    resp = client.get("/api/emails/1")
    assert resp.status_code == 404


# ---- Logout behavior (client-side token removal) ----

def test_logout_removes_token_from_header(client):
    """Simulate frontend logout: remove Authorization header, requests become 401."""
    r = client.post("/api/auth/register", json={"email": "logout@test.dev", "password": "123456"})
    token = r.json()["access_token"]

    # Authenticated request works
    client.headers["Authorization"] = f"Bearer {token}"
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200

    # Simulate logout: clear the header
    del client.headers["Authorization"]

    # Unauthenticated request should be rejected
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_does_not_invalidate_token(client):
    """JWT cannot be revoked without a blacklist. After 'logout' the old token
    still works on new requests if re-attached. This is expected JWT behavior."""
    r = client.post("/api/auth/register", json={"email": "jwt@test.dev", "password": "123456"})
    token = r.json()["access_token"]

    # Use token successfully
    client.headers["Authorization"] = f"Bearer {token}"
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200

    # Simulate logout (drop header)
    del client.headers["Authorization"]

    # Re-attach the same token - it still works (JWT is stateless)
    client.headers["Authorization"] = f"Bearer {token}"
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
