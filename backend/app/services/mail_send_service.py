"""Send emails via connected Gmail or Outlook accounts."""
from __future__ import annotations

import base64
import logging
from email.mime.text import MIMEText
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.db.models import Draft, GmailAccount, OutlookAccount
from app.core import crypto

logger = logging.getLogger(__name__)


class SendError(Exception):
    pass


def send_draft(db: Session, draft_id: int, user_id: int) -> Draft:
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
    if not draft:
        raise SendError("Draft not found")
    if draft.status == "sent":
        raise SendError("Draft already sent")

    gmail = db.query(GmailAccount).filter(GmailAccount.user_id == user_id).first()
    outlook = db.query(OutlookAccount).filter(OutlookAccount.user_id == user_id).first()

    try:
        if gmail:
            _send_via_gmail(draft, gmail)
        elif outlook:
            _send_via_outlook(draft, outlook, db)
        else:
            raise SendError("No connected mailbox. Connect Gmail or Outlook in Settings first.")
        draft.status = "sent"
        draft.updated_at = None  # trigger onupdate
    except SendError:
        draft.status = "send_failed"
        db.commit()
        raise
    except Exception as exc:
        logger.error("Unexpected send error: %s", exc)
        draft.status = "send_failed"
        db.commit()
        raise SendError(str(exc))

    db.commit()
    db.refresh(draft)
    return draft


# -- Gmail send via Gmail API --

def _send_via_gmail(draft: Draft, account: GmailAccount):
    token = crypto.decrypt(account.access_token)
    if not token:
        raise SendError("Gmail access token not available. Refresh token first.")

    msg = MIMEText(draft.content)
    msg["To"] = draft.email.sender if draft.email else ""
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

def _send_via_outlook(draft: Draft, account: OutlookAccount, db: Session):
    token = crypto.decrypt(account.access_token)
    if not token:
        raise SendError("Outlook access token not available. Refresh token first.")

    body = {
        "message": {
            "subject": f"Re: {draft.email.subject}" if draft.email else "",
            "body": {"contentType": "Text", "content": draft.content},
            "toRecipients": [
                {"emailAddress": {"address": draft.email.sender or ""}}
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
