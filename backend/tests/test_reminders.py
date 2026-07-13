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


def test_bulk_complete_reminders(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    reminder_ids = [item["id"] for item in auth_client.get("/api/reminders").json()["items"]]

    resp = auth_client.post("/api/reminders/bulk", json={"reminder_ids": reminder_ids, "action": "complete"})

    assert resp.status_code == 200
    assert resp.json()["updated"] == len(reminder_ids)
    items = auth_client.get("/api/reminders?status=done").json()["items"]
    assert {item["id"] for item in items} >= set(reminder_ids)


def test_bulk_delete_reminders(auth_client):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    reminder_ids = [item["id"] for item in auth_client.get("/api/reminders").json()["items"]]

    resp = auth_client.post("/api/reminders/bulk", json={"reminder_ids": reminder_ids, "action": "delete"})

    assert resp.status_code == 200
    assert resp.json()["updated"] == len(reminder_ids)
    assert auth_client.get("/api/reminders").json()["total"] == 0


def test_bulk_reminders_are_user_isolated(auth_client, client, db_session):
    setup_email(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    reminder_id = auth_client.get("/api/reminders").json()["items"][0]["id"]

    second = client.post("/api/auth/register", json={"email": "second@test.dev", "password": "123456"})
    client.headers["Authorization"] = f"Bearer {second.json()['access_token']}"
    resp = client.post("/api/reminders/bulk", json={"reminder_ids": [reminder_id], "action": "delete"})

    assert resp.status_code == 200
    assert resp.json()["updated"] == 0
    assert resp.json()["not_found"] == 1
