from app.services.mail_send_service import send_draft, SendError


class TestSendDraft:
    def test_send_draft_not_found(self, db_session):
        import pytest
        with pytest.raises(SendError, match="Draft not found"):
            send_draft(db_session, draft_id=9999, user_id=1)

    def test_send_no_mailbox_connected(self, auth_client):
        """No Gmail/Outlook connected: should return 400 with error detail."""
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        resp = auth_client.post("/api/drafts/1/send")
        assert resp.status_code == 400
        assert "No connected mailbox" in resp.json()["detail"]

    def test_send_already_sent_fails(self, auth_client, db_session):
        """Already sent drafts cannot be sent again."""
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        from app.db.models import Draft
        draft = db_session.query(Draft).first()
        draft.status = "sent"
        db_session.commit()
        resp = auth_client.post("/api/drafts/1/send")
        assert resp.status_code == 400
        assert "already sent" in resp.json()["detail"]

    def test_send_failure_persists_error(self, auth_client, db_session):
        """Failed send stores error on draft for display after page refresh."""
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        auth_client.post("/api/drafts/1/send")
        from app.db.models import Draft
        draft = db_session.query(Draft).first()
        assert draft.status == "send_failed"
        assert draft.send_error is not None
        assert "No connected mailbox" in draft.send_error

    def test_send_failed_draft_can_be_resent(self, auth_client, db_session):
        """send_failed draft can be sent again (retries, not blocked)."""
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        auth_client.post("/api/drafts/1/send")
        from app.db.models import Draft
        draft = db_session.query(Draft).first()
        assert draft.status == "send_failed"
        # Retry should also fail (no mailbox), but not 404 or already-sent
        resp = auth_client.post("/api/drafts/1/send")
        assert resp.status_code == 400
