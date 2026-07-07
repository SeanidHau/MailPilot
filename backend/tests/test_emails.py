def test_import_emails(client):
    resp = client.post("/api/emails/import")
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 8


def test_import_emails_deduplicate(client):
    client.post("/api/emails/import")
    resp = client.post("/api/emails/import")
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 0


def test_list_emails(client):
    client.post("/api/emails/import")
    resp = client.get("/api/emails")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 8
    assert len(data["items"]) <= 20


def test_list_emails_pagination(client):
    client.post("/api/emails/import")
    resp = client.get("/api/emails?page=1&page_size=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) == 3
    assert data["total"] == 8


def test_list_emails_search(client):
    client.post("/api/emails/import")
    resp = client.get("/api/emails?q=budget")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "budget" in data["items"][0]["subject"].lower()


def test_list_emails_filter_category(client):
    client.post("/api/emails/import")
    resp = client.get("/api/emails?category=normal")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["category"] == "normal"


def test_list_emails_filter_read(client):
    client.post("/api/emails/import")
    resp = client.get("/api/emails?is_read=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 8


def test_list_emails_filter_importance(client):
    client.post("/api/emails/import")
    resp = client.get("/api/emails?min_importance=3")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["importance_score"] >= 3


def test_get_email_detail(client):
    client.post("/api/emails/import")
    resp = client.get("/api/emails/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "sender" in data
    assert "body" in data
    assert "drafts" in data
    assert "reminders" in data


def test_get_email_not_found(client):
    resp = client.get("/api/emails/9999")
    assert resp.status_code == 404


def test_patch_email_is_read(client):
    client.post("/api/emails/import")
    resp = client.patch("/api/emails/1", json={"is_read": True})
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


def test_patch_email_category(client):
    client.post("/api/emails/import")
    resp = client.patch("/api/emails/1", json={"category": "important"})
    assert resp.status_code == 200
    assert resp.json()["category"] == "important"


def test_patch_email_invalid_score(client):
    client.post("/api/emails/import")
    resp = client.patch("/api/emails/1", json={"importance_score": 9})
    assert resp.status_code == 422


def test_classify_email(client):
    client.post("/api/emails/import")
    resp = client.post("/api/emails/1/classify")
    assert resp.status_code == 200
    data = resp.json()
    assert "category" in data
    assert "importance_score" in data


def test_summarize_email(client):
    client.post("/api/emails/import")
    resp = client.post("/api/emails/1/summarize")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["summary"]) > 0
