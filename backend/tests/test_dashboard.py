def setup_data(auth_client):
    auth_client.post("/api/emails/import")
    auth_client.post("/api/emails/1/classify")


def test_dashboard_summary(auth_client):
    setup_data(auth_client)
    resp = auth_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_emails" in data
    assert "pending_emails" in data
    assert "important_emails" in data
    assert "pending_reminders" in data
    assert "recent_important_emails" in data
    assert "upcoming_reminders" in data
    assert data["total_emails"] == 8
    assert data["pending_emails"] == 8


def test_dashboard_after_classify(auth_client):
    setup_data(auth_client)
    resp = auth_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    assert resp.json()["important_emails"] >= 1


def test_dashboard_with_reminders(auth_client):
    setup_data(auth_client)
    auth_client.post("/api/emails/1/reminders/extract")
    resp = auth_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    assert resp.json()["pending_reminders"] >= 1


def test_dashboard_all_read_not_empty(auth_client):
    """Emails exist but all are read: total_emails > 0, should NOT show empty state."""
    setup_data(auth_client)
    # Mark all emails as read
    for i in range(1, 9):
        auth_client.patch(f"/api/emails/{i}", json={"is_read": True})
    resp = auth_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_emails"] == 8
    assert data["pending_emails"] == 0
    # total_emails > 0 even though pending_emails == 0
    # Frontend should use total_emails to determine empty state


def test_dashboard_no_emails_zero_total(auth_client):
    """No emails imported: total_emails == 0."""
    resp = auth_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    assert resp.json()["total_emails"] == 0
