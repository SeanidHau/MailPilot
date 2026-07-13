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


def test_create_manual_draft(auth_client):
    resp = auth_client.post("/api/drafts", json={
        "recipient": "friend@example.com",
        "subject": "项目更新",
        "content": "您好，向您同步最新进展。",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_id"] is None
    assert data["tone"] == "manual"
    assert data["recipient"] == "friend@example.com"
    assert data["subject"] == "项目更新"
    assert data["status"] == "draft"


def test_create_manual_draft_rejects_invalid_recipient(auth_client):
    resp = auth_client.post("/api/drafts", json={
        "recipient": "not-an-email",
        "subject": "主题",
        "content": "正文",
    })
    assert resp.status_code == 422


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


def test_delete_draft_soft_deletes_and_hides_from_list(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/drafts", json={"tone": "formal"})

    resp = auth_client.delete("/api/drafts/1")
    assert resp.status_code == 200
    assert resp.json() == {"status": "deleted"}

    list_resp = auth_client.get("/api/drafts")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0

    detail_resp = auth_client.get("/api/drafts/1")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "deleted"
