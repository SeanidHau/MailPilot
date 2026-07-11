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


def send_draft(db: Session, draft_id: int, user_id: int) -> Draft:
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
    if not draft:
        raise SendError("Draft not found")
    if draft.status == "sent":
        raise SendError("Draft already sent")

    from app.db.models import GmailAccount, OutlookAccount
    gmail = db.query(GmailAccount).filter(GmailAccount.user_id == user_id).first()
    outlook = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()

    def fail(msg: str):
        draft.status = "send_failed"
        draft.send_error = msg
        db.commit()
        raise SendError(msg)

    try:
        if gmail:
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
    if not draft.email:
        return ""
    _, addr = parseaddr(draft.email.sender)
    return addr or draft.email.sender


# -- Gmail send via Gmail API --

def _send_via_gmail(draft: Draft, db: Session):
    token = get_gmail_token(db, draft.user_id)

    msg = MIMEText(draft.content)
    msg["To"] = _get_recipient_address(draft)
    msg["Subject"] = f"Re: {draft.email.subject}" if draft.email else ""
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = httpx.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"raw": raw},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise SendError(f"Gmail send failed ({resp.status_code}): {resp.text[:200]}")


# -- Outlook send via Microsoft Graph --

def _send_via_outlook(draft: Draft, db: Session):
    token = get_outlook_token(db, draft.user_id)

    body = {
        "message": {
            "subject": f"Re: {draft.email.subject}" if draft.email else "",
            "body": {"contentType": "Text", "content": draft.content},
            "toRecipients": [
                {"emailAddress": {"address": _get_recipient_address(draft)}}
            ] if draft.email else [],
        },
        "saveToSentItems": True,
    }

    resp = httpx.post(
        "https://graph.microsoft.com/v1.0/me/sendMail",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=30,
    )
    if resp.status_code >= 400:
        raise SendError(f"Outlook send failed ({resp.status_code}): {resp.text[:200]}")
