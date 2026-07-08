def setup_email(auth_client):
    auth_client.post("/api/emails/import")


def test_extract_reminders(auth_client):
    setup_email(auth_client)
    resp = auth_client.post("/api/emails/1/reminders/extract")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["reminders"]) >= 1


def test_list_reminders(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    resp = auth_client.get("/api/reminders")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_complete_reminder(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    resp = auth_client.patch("/api/reminders/1", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_delete_reminder(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    resp = auth_client.delete("/api/reminders/1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_filter_reminders_by_status(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    auth_client.patch("/api/reminders/1", json={"status": "done"})
    resp = auth_client.get("/api/reminders?status=done")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "done"
