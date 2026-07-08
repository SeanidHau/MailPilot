def setup_email(auth_client):
    auth_client.post("/api/emails/import")


def test_generate_draft(auth_client):
    setup_email(auth_client)
    resp = auth_client.post("/api/emails/1/drafts", json={"tone": "formal"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tone"] == "formal"
    assert len(data["content"]) > 0
    assert "id" in data


def test_generate_draft_invalid_tone(auth_client):
    setup_email(auth_client)
    resp = auth_client.post("/api/emails/1/drafts", json={"tone": "angry"})
    assert resp.status_code == 422


def test_list_drafts(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/drafts", json={"tone": "formal"})
    auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
    resp = auth_client.get("/api/drafts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2


def test_get_draft(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/drafts", json={"tone": "formal"})
    resp = auth_client.get("/api/drafts/1")
    assert resp.status_code == 200
    assert resp.json()["tone"] == "formal"


def test_patch_draft(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/drafts", json={"tone": "formal"})
    resp = auth_client.patch("/api/drafts/1", json={"content": "Edited reply", "status": "saved"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "Edited reply"
    assert data["status"] == "saved"
