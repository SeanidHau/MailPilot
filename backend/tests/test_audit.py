import json

from app.db.models import AuditLog


class TestAuditLog:
    def test_import_creates_audit_entry(self, auth_client, db_session):
        resp = auth_client.post("/api/emails/import")
        assert resp.status_code == 202
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
        resp = auth_client.patch("/api/emails/1", json={"category": "spam"})
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
        r = client.post("/api/auth/register", json={"email": "auditb@test.dev", "password": "123456"})
        token_b = r.json()["access_token"]
        resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestAIMetadata:
    def test_classify_stores_metadata(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/classify")
        from app.db.models import Email
        email = db_session.query(Email).filter(Email.id == 1).first()
        assert email.ai_metadata is not None
        md = json.loads(email.ai_metadata)
        assert md["prompt_version"] == "1.2.0"
        assert "provider" in md
        assert "generated_at" in md

    def test_summarize_stores_metadata(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/summarize")
        from app.db.models import Email
        email = db_session.query(Email).filter(Email.id == 1).first()
        assert email.ai_metadata is not None
        md = json.loads(email.ai_metadata)
        assert md["prompt_version"] == "1.2.0"

    def test_draft_generate_stores_metadata(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        from app.db.models import Draft
        draft = db_session.query(Draft).first()
        assert draft.ai_metadata is not None
        md = json.loads(draft.ai_metadata)
        assert md["prompt_version"] == "1.2.0"

    def test_reminder_extract_stores_metadata(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/reminders/extract")
        from app.db.models import Reminder
        reminder = db_session.query(Reminder).first()
        assert reminder.ai_metadata is not None
        md = json.loads(reminder.ai_metadata)
        assert md["prompt_version"] == "1.2.0"
