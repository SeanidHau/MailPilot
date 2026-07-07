def setup_data(client):
    client.post("/api/emails/import")
    client.post("/api/emails/1/classify")


def test_dashboard_summary(client):
    setup_data(client)
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "pending_emails" in data
    assert "important_emails" in data
    assert "pending_reminders" in data
    assert "recent_important_emails" in data
    assert "upcoming_reminders" in data
    assert data["pending_emails"] == 8


def test_dashboard_after_classify(client):
    setup_data(client)
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    assert resp.json()["important_emails"] >= 1


def test_dashboard_with_reminders(client):
    setup_data(client)
    client.post("/api/emails/1/reminders/extract")
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    assert resp.json()["pending_reminders"] >= 1
