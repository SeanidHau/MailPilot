from app.db.models import AuditLog


class TestAuditLog:
    def test_import_creates_audit_entry(self, auth_client, db_session):
        resp = auth_client.post("/api/emails/import")
        assert resp.status_code == 200
        logs = db_session.query(AuditLog).filter(AuditLog.action == "email_import").all()
        assert len(logs) >= 1
        assert logs[0].detail == "imported 8"

    def test_classify_creates_audit_entry(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        resp = auth_client.post("/api/emails/1/classify")
        assert resp.status_code == 200
        logs = db_session.query(AuditLog).filter(AuditLog.action == "email_classify").all()
        assert len(logs) >= 1

    def test_summarize_creates_audit_entry(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        resp = auth_client.post("/api/emails/1/summarize")
        assert resp.status_code == 200
        logs = db_session.query(AuditLog).filter(AuditLog.action == "email_summarize").all()
        assert len(logs) >= 1

    def test_draft_generate_creates_audit_entry(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        resp = auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        assert resp.status_code == 200
        logs = db_session.query(AuditLog).filter(AuditLog.action == "draft_generate").all()
        assert len(logs) >= 1

    def test_reminder_extract_creates_audit_entry(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        resp = auth_client.post("/api/emails/1/reminders/extract")
        assert resp.status_code == 200
        logs = db_session.query(AuditLog).filter(AuditLog.action == "reminder_extract").all()
        assert len(logs) >= 1

    def test_category_change_creates_audit_entry(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        resp = auth_client.patch("/api/emails/1", json={"category": "important"})
        assert resp.status_code == 200
        logs = db_session.query(AuditLog).filter(AuditLog.action == "category_change").all()
        assert len(logs) >= 1

    def test_get_audit_endpoint(self, auth_client):
        auth_client.post("/api/emails/import")
        resp = auth_client.get("/api/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "items" in data

    def test_audit_is_user_scoped(self, auth_client, client, db_session):
        """User A cannot see User B's audit logs."""
        auth_client.post("/api/emails/import")
        # Register user B
        r = client.post("/api/auth/register", json={"email": "auditb@test.dev", "password": "123456"})
        token_b = r.json()["access_token"]
        resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
