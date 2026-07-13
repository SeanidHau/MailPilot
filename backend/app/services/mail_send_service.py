"""Send emails via connected Gmail or Outlook accounts."""
from __future__ import annotations

import base64
import logging
from email.mime.text import MIMEText
from email.utils import parseaddr
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.db.models import Draft
from app.services import audit_service
from app.services.gmail_service import get_valid_access_token as get_gmail_token
from app.services.outlook_service import get_valid_access_token as get_outlook_token

logger = logging.getLogger(__name__)


class SendError(Exception):
    pass


SENDABLE_STATUSES = {"draft", "saved", "ready_to_send", "send_failed"}


def send_draft(
    db: Session,
    draft_id: int,
    user_id: int,
    provider: Optional[str] = None,
) -> Draft:
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
    if not draft:
        raise SendError("Draft not found")
    if draft.status == "sent":
        raise SendError("Draft already sent")
    if draft.status == "deleted":
        raise SendError("Deleted drafts cannot be sent")
    if draft.status not in SENDABLE_STATUSES:
        raise SendError(f"Draft cannot be sent in status: {draft.status}")
    if not draft.content or not draft.content.strip():
        raise SendError("Draft content is empty")

    from app.db.models import GmailAccount, OutlookAccount
    gmail = db.query(GmailAccount).filter(GmailAccount.user_id == user_id).first()
    outlook = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()

    def fail(msg: str):
        draft.status = "send_failed"
        draft.send_error = msg
        db.commit()
        raise SendError(msg)

    try:
        if provider == "gmail":
            if not gmail:
                fail("Gmail mailbox is not connected. Connect Gmail in Settings first.")
            _send_via_gmail(draft, db)
        elif provider == "outlook":
            if not outlook:
                fail("Outlook mailbox is not connected. Connect Outlook in Settings first.")
            _send_via_outlook(draft, db)
        elif gmail:
            # Keep the API backwards-compatible for clients that do not send a provider.
            _send_via_gmail(draft, db)
        elif outlook:
            _send_via_outlook(draft, db)
        else:
            fail("No connected mailbox. Connect Gmail or Outlook in Settings first.")
        draft.status = "sent"
        draft.send_error = None
    except SendError as exc:
        draft.status = "send_failed"
        draft.send_error = str(exc)
        db.commit()
        raise
    except Exception as exc:
        logger.error("Unexpected send error: %s", exc)
        fail(str(exc))

    audit_service.log_action(db, user_id, "draft_send", "draft", draft_id, f"email={draft.email_id}")
    db.commit()
    db.refresh(draft)
    return draft


def _get_recipient_address(draft: Draft) -> str:
    raw_recipient = draft.recipient or (draft.email.sender if draft.email else "")
    _, addr = parseaddr(raw_recipient)
    return addr or raw_recipient


def _get_subject(draft: Draft) -> str:
    if draft.subject is not None:
        return draft.subject.strip()
    return f"Re: {draft.email.subject}" if draft.email else ""


def _require_recipient(draft: Draft) -> str:
    recipient = _get_recipient_address(draft).strip()
    if not recipient or "@" not in recipient:
        raise SendError("Draft recipient is missing or invalid")
    return recipient


# -- Gmail send via Gmail API --

def _send_via_gmail(draft: Draft, db: Session):
    token = get_gmail_token(db, draft.user_id)

    recipient = _require_recipient(draft)
    subject = _get_subject(draft)
    if not subject:
        raise SendError("Draft subject is empty")
    msg = MIMEText(draft.content, "plain", "utf-8")
    msg["To"] = recipient
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = httpx.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"raw": raw},
        timeout=30,
        trust_env=True,
    )
    if resp.status_code >= 400:
        raise SendError(f"Gmail send failed ({resp.status_code}): {resp.text[:200]}")


# -- Outlook send via Microsoft Graph --

def _send_via_outlook(draft: Draft, db: Session):
    token = get_outlook_token(db, draft.user_id)
    recipient = _require_recipient(draft)
    subject = _get_subject(draft)
    if not subject:
        raise SendError("Draft subject is empty")

    body = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": draft.content},
            "toRecipients": [
                {"emailAddress": {"address": recipient}}
            ],
        },
        "saveToSentItems": True,
    }

    resp = httpx.post(
        "https://graph.microsoft.com/v1.0/me/sendMail",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=30,
        trust_env=True,
    )
    if resp.status_code >= 400:
        raise SendError(f"Outlook send failed ({resp.status_code}): {resp.text[:200]}")
