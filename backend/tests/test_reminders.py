def setup_email(client):
    client.post("/api/emails/import")


def test_extract_reminders(client):
    setup_email(client)
    resp = client.post("/api/emails/1/reminders/extract")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["reminders"]) >= 1


def test_list_reminders(client):
    setup_email(client)
    client.post("/api/emails/1/reminders/extract")
    resp = client.get("/api/reminders")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_complete_reminder(client):
    setup_email(client)
    client.post("/api/emails/1/reminders/extract")
    resp = client.patch("/api/reminders/1", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_delete_reminder(client):
    setup_email(client)
    client.post("/api/emails/1/reminders/extract")
    resp = client.delete("/api/reminders/1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_filter_reminders_by_status(client):
    setup_email(client)
    client.post("/api/emails/1/reminders/extract")
    client.patch("/api/reminders/1", json={"status": "done"})
    resp = client.get("/api/reminders?status=done")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "done"
