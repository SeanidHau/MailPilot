def get_completed_job(client, response):
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    job_response = client.get(f"/api/jobs/{job_id}")
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    return job


def test_import_emails(auth_client):
    job = get_completed_job(auth_client, auth_client.post("/api/emails/import"))
    assert job["result"]["imported"] == 8


def test_import_automatically_processes_email(auth_client, db_session):
    resp = auth_client.post("/api/emails/import")
    get_completed_job(auth_client, resp)

    from app.db.models import Email, Reminder

    email = db_session.query(Email).filter(Email.message_id == "msg-001@mock").one()
    assert email.category == "important"
    assert email.summary
    assert email.ai_metadata is not None
    assert db_session.query(Reminder).filter(Reminder.email_id == email.id).count() >= 1


def test_import_emails_deduplicate(auth_client):
    get_completed_job(auth_client, auth_client.post("/api/emails/import"))
    job = get_completed_job(auth_client, auth_client.post("/api/emails/import"))
    assert job["result"]["imported"] == 0


def test_list_emails(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 8
    assert len(data["items"]) <= 20


def test_list_emails_pagination(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails?page=1&page_size=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) == 3
    assert data["total"] == 8


def test_list_emails_search(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails?q=budget")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "budget" in data["items"][0]["subject"].lower()


def test_list_emails_filter_category(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails?category=normal")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["category"] == "normal"


def test_list_emails_filter_read(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails?is_read=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 8


def test_list_emails_filter_importance(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails?min_importance=3")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["importance_score"] >= 3


def test_list_emails_sorts_by_importance(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails?sort_by=importance&sort_order=desc")
    assert resp.status_code == 200
    scores = [item["importance_score"] for item in resp.json()["items"]]
    assert scores == sorted(scores, reverse=True)


def test_list_emails_sorts_by_received_at_ascending(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails?sort_by=received_at&sort_order=asc")
    assert resp.status_code == 200
    received_at = [item["received_at"] for item in resp.json()["items"]]
    assert received_at == sorted(received_at)


def test_list_emails_rejects_invalid_sort(auth_client):
    resp = auth_client.get("/api/emails?sort_by=sender")
    assert resp.status_code == 422


def test_get_email_detail(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.get("/api/emails/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "sender" in data
    assert "body" in data
    assert "drafts" in data
    assert "reminders" in data


def test_get_email_not_found(auth_client):
    resp = auth_client.get("/api/emails/9999")
    assert resp.status_code == 404


def test_patch_email_is_read(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.patch("/api/emails/1", json={"is_read": True})
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


def test_patch_email_category(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.patch("/api/emails/1", json={"category": "important"})
    assert resp.status_code == 200
    assert resp.json()["category"] == "important"


def test_patch_email_invalid_score(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.patch("/api/emails/1", json={"importance_score": 9})
    assert resp.status_code == 422


def test_bulk_mark_read(auth_client):
    auth_client.post("/api/emails/import")

    resp = auth_client.post("/api/emails/bulk", json={"email_ids": [1, 2], "action": "mark_read"})
    assert resp.status_code == 200
    assert resp.json()["updated"] == 2

    unread = auth_client.get("/api/emails?is_read=false").json()
    assert unread["total"] == 6


def test_bulk_delete_soft_deletes_and_hides_emails(auth_client):
    auth_client.post("/api/emails/import")

    resp = auth_client.post("/api/emails/bulk", json={"email_ids": [1, 2], "action": "delete"})
    assert resp.status_code == 200
    assert resp.json()["updated"] == 2

    emails = auth_client.get("/api/emails").json()
    assert emails["total"] == 6
    assert auth_client.get("/api/emails/1").status_code == 404


def test_bulk_action_rejects_invalid_action(auth_client):
    resp = auth_client.post("/api/emails/bulk", json={"email_ids": [1], "action": "archive"})
    assert resp.status_code == 422


def test_classify_email(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.post("/api/emails/1/classify")
    assert resp.status_code == 200
    data = resp.json()
    assert "category" in data
    assert "importance_score" in data


def test_summarize_email(auth_client):
    auth_client.post("/api/emails/import")
    resp = auth_client.post("/api/emails/1/summarize")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["summary"]) > 0
