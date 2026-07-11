from unittest.mock import patch, MagicMock
import pytest
from app.services.mail_send_service import send_draft, SendError


class TestSendDraft:
    def test_send_draft_not_found(self, db_session):
        with pytest.raises(SendError, match="Draft not found"):
            send_draft(db_session, draft_id=9999, user_id=1)

    def test_send_no_mailbox_connected(self, auth_client):
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        resp = auth_client.post("/api/drafts/1/send")
        assert resp.status_code == 400
        assert "No connected mailbox" in resp.json()["detail"]

    def test_send_already_sent_fails(self, auth_client, db_session):
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
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        auth_client.post("/api/drafts/1/send")
        from app.db.models import Draft
        draft = db_session.query(Draft).first()
        assert draft.status == "send_failed"
        assert draft.send_error is not None
        assert "No connected mailbox" in draft.send_error

    def test_send_failed_draft_can_be_resent(self, auth_client, db_session):
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/1/drafts", json={"tone": "brief"})
        auth_client.post("/api/drafts/1/send")
        from app.db.models import Draft
        draft = db_session.query(Draft).first()
        assert draft.status == "send_failed"
        resp = auth_client.post("/api/drafts/1/send")
        assert resp.status_code == 400

    # -- Mock-based tests for Gmail send paths (mock HTTP, real DB records) --

    @patch("app.services.mail_send_service._send_via_gmail")
    @patch("app.services.mail_send_service.get_gmail_token")
    def test_gmail_api_failure_persists_send_failed(self, mock_get_token, mock_send, db_session):
        """Gmail API 500 -> draft.status = send_failed, draft.send_error populated."""
        from datetime import datetime
        from app.db.models import Draft, Email, GmailAccount
        email = Email(message_id="t1", sender="a@b.com", recipients="c@b.com",
                       subject="S", body="B", received_at=datetime(2026, 1, 1), user_id=1)
        db_session.add(email)
        db_session.add(GmailAccount(user_id=1, email="a@b.com", access_token=encrypt("tok"), refresh_token=encrypt("ref")))
        draft = Draft(email_id=1, tone="brief", content="Hi", user_id=1)
        db_session.add(draft)
        db_session.commit()

        mock_get_token.return_value = "valid-token"
        mock_send.side_effect = SendError("Gmail send failed (500): server error")

        with pytest.raises(SendError, match="Gmail send failed"):
            send_draft(db_session, draft.id, user_id=1)

        db_session.refresh(draft)
        assert draft.status == "send_failed"
        assert "Gmail send failed" in (draft.send_error or "")

    @patch("app.services.mail_send_service._send_via_gmail")
    @patch("app.services.mail_send_service.get_gmail_token")
    def test_gmail_send_success(self, mock_get_token, mock_send, db_session):
        """Successful Gmail send -> draft.status = sent, send_error = None."""
        from datetime import datetime
        from app.db.models import Draft, Email, GmailAccount
        email = Email(message_id="t2", sender="a@b.com", recipients="c@b.com",
                       subject="S", body="B", received_at=datetime(2026, 1, 1), user_id=1)
        db_session.add(email)
        db_session.add(GmailAccount(user_id=1, email="a@b.com", access_token=encrypt("tok"), refresh_token=encrypt("ref")))
        draft = Draft(email_id=1, tone="brief", content="Hi", user_id=1)
        db_session.add(draft)
        db_session.commit()

        mock_get_token.return_value = "valid-token"
        mock_send.return_value = None
        result = send_draft(db_session, draft.id, user_id=1)
        assert result.status == "sent"
        assert result.send_error is None

    @patch("app.services.mail_send_service.get_gmail_token")
    def test_token_decrypt_failure(self, mock_get_token, db_session):
        """Corrupted/unavailable token -> SendError raised, draft marked send_failed."""
        from datetime import datetime
        from app.db.models import Draft, Email, GmailAccount
        email = Email(message_id="t3", sender="a@b.com", recipients="c@b.com",
                       subject="S", body="B", received_at=datetime(2026, 1, 1), user_id=1)
        db_session.add(email)
        db_session.add(GmailAccount(user_id=1, email="a@b.com", access_token=encrypt("tok"), refresh_token=encrypt("ref")))
        draft = Draft(email_id=1, tone="brief", content="Hi", user_id=1)
        db_session.add(draft)
        db_session.commit()

        mock_get_token.side_effect = SendError("access token not available")

        with pytest.raises(SendError, match="access token not available"):
            send_draft(db_session, draft.id, user_id=1)

        db_session.refresh(draft)
        assert draft.status == "send_failed"
        assert "access token" in (draft.send_error or "")


from app.core.crypto import encrypt
