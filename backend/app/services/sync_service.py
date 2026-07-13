"""Mailbox sync: fetch inbox, incremental updates, dedup by provider message ID."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.db.models import Email, User
from app.services import email_service
from app.services.gmail_service import get_valid_access_token as get_gmail_token
from app.services.outlook_service import get_valid_access_token as get_outlook_token

logger = logging.getLogger(__name__)

GMAIL_PAGE_SIZE = 500
OUTLOOK_PAGE_SIZE = 100


class SyncResult:
    def __init__(self):
        self.new: int = 0
        self.skipped: int = 0
        self.errors: list[str] = []
        self.new_email_ids: list[int] = []


def sync_gmail_inbox(db: Session, user_id: int) -> SyncResult:
    result = SyncResult()
    token = get_gmail_token(db, user_id)

    # Get messages list from inbox
    msg_ids = _gmail_list_messages(token, result)
    if not msg_ids:
        return result

    for msg_id in msg_ids:
        try:
            msg = _gmail_get_message(token, msg_id, result)
            if not msg:
                continue
            _upsert_email(db, user_id, "gmail", msg, result)
        except Exception as exc:
            result.errors.append(f"gmail:{msg_id}: {exc}")

    db.commit()
    result.errors.extend(email_service.process_emails_with_ai(db, user_id, result.new_email_ids))
    return result


def sync_outlook_inbox(db: Session, user_id: int) -> SyncResult:
    result = SyncResult()
    token = get_outlook_token(db, user_id)

    messages = _outlook_list_messages(token, result)
    if not messages:
        return result

    for msg in messages:
        try:
            msg_id = msg.get("id", "")
            if not msg_id:
                continue
            _upsert_email(db, user_id, "outlook", msg, result)
        except Exception as exc:
            result.errors.append(f"outlook:{msg.get('id','')}: {exc}")

    db.commit()
    result.errors.extend(email_service.process_emails_with_ai(db, user_id, result.new_email_ids))
    return result


# -- Gmail API helpers --

def _gmail_list_messages(token: str, result: SyncResult) -> list[str]:
    message_ids: list[str] = []
    page_token: str | None = None
    try:
        while True:
            params: dict[str, Any] = {
                "maxResults": GMAIL_PAGE_SIZE,
                "labelIds": "INBOX",
            }
            if page_token:
                params["pageToken"] = page_token

            resp = httpx.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=20,
                trust_env=True,
            )
            resp.raise_for_status()
            data = resp.json()
            message_ids.extend(m["id"] for m in data.get("messages", []) if m.get("id"))
            page_token = data.get("nextPageToken")
            if not page_token:
                return message_ids
    except httpx.HTTPStatusError as exc:
        result.errors.append(f"Gmail list failed: {exc.response.status_code}")
    except Exception as exc:
        result.errors.append(f"Gmail list error: {exc}")
    return message_ids


def _gmail_get_message(token: str, msg_id: str, result: SyncResult) -> dict | None:
    try:
        resp = httpx.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"format": "full"},
            timeout=15,
            trust_env=True,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        result.errors.append(f"gmail fetch {msg_id}: {exc}")
        return None


# -- Outlook / MS Graph helpers --

def _outlook_list_messages(token: str, result: SyncResult) -> list[dict]:
    messages: list[dict] = []
    next_url: str | None = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
    params: dict[str, Any] | None = {
        "$top": OUTLOOK_PAGE_SIZE,
        "$orderby": "receivedDateTime desc",
        "$select": "id,from,toRecipients,subject,body,isRead,receivedDateTime,hasAttachments",
        "$expand": "attachments($select=name,contentType,size)",
    }
    try:
        while next_url:
            resp = httpx.get(
                next_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Prefer": 'outlook.body-content-type="text"',
                },
                params=params,
                timeout=20,
                trust_env=True,
            )
            resp.raise_for_status()
            data = resp.json()
            messages.extend(data.get("value", []))
            next_url = data.get("@odata.nextLink")
            # Graph nextLink already contains the original query and its
            # continuation token; do not append the first-page parameters.
            params = None
        return messages
    except httpx.HTTPStatusError as exc:
        result.errors.append(f"Outlook list failed: {exc.response.status_code}")
    except Exception as exc:
        result.errors.append(f"Outlook list error: {exc}")
    return messages


# -- Shared upsert --

def _upsert_email(db: Session, user_id: int, provider: str, raw: dict, result: SyncResult):
    provider_msg_id = raw.get("id", "")
    if not provider_msg_id:
        result.skipped += 1
        return

    # Dedup by provider + provider_message_id + user_id
    existing = (
        db.query(Email)
        .filter(
            Email.user_id == user_id,
            Email.provider == provider,
            Email.provider_message_id == provider_msg_id,
        )
        .first()
    )
    attachments_json = _extract_attachments(provider, raw)

    if existing:
        new_read = _extract_is_read(provider, raw)
        if existing.is_read != new_read or existing.attachments != attachments_json:
            existing.is_read = new_read
            existing.attachments = attachments_json
            db.add(existing)
        result.skipped += 1
        return

    email = Email(
        message_id=f"{provider}:{provider_msg_id}",
        provider=provider,
        provider_message_id=provider_msg_id,
        sender=_extract_sender(provider, raw),
        recipients=_extract_recipients(provider, raw),
        subject=_extract_subject(provider, raw) or "(no subject)",
        body=_extract_body(provider, raw) or "",
        received_at=_extract_received_at(provider, raw) or datetime.now(timezone.utc),
        is_read=_extract_is_read(provider, raw),
        imported_source=provider,
        user_id=user_id,
        attachments=attachments_json,
    )
    db.add(email)
    db.flush()
    result.new_email_ids.append(email.id)
    result.new += 1


def _extract_sender(provider: str, raw: dict) -> str:
    if provider == "gmail":
        headers = raw.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name") == "From":
                return h.get("value", "")
        return ""
    if provider == "outlook":
        fr = raw.get("from", {})
        addr = fr.get("emailAddress", {})
        name = addr.get("name", "")
        email_addr = addr.get("address", "")
        return f"{name} <{email_addr}>" if name else email_addr
    return ""


def _extract_recipients(provider: str, raw: dict) -> str:
    if provider == "gmail":
        headers = raw.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name") == "To":
                return h.get("value", "")
        return ""
    if provider == "outlook":
        to_list = raw.get("toRecipients", [])
        parts = []
        for r in to_list:
            addr = r.get("emailAddress", {})
            name = addr.get("name", "")
            e = addr.get("address", "")
            parts.append(f"{name} <{e}>" if name else e)
        return ", ".join(parts)
    return ""


def _extract_subject(provider: str, raw: dict) -> str:
    if provider == "gmail":
        headers = raw.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name") == "Subject":
                return h.get("value", "")
        return ""
    if provider == "outlook":
        return raw.get("subject", "")
    return ""


def _extract_body(provider: str, raw: dict) -> str:
    if provider == "gmail":
        payload = raw.get("payload", {})
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                import base64
                return base64.urlsafe_b64decode(data + "==").decode(errors="replace")
        # Try parts
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    import base64
                    return base64.urlsafe_b64decode(data + "==").decode(errors="replace")
        # Fallback: snippet
        return raw.get("snippet", "")
    if provider == "outlook":
        body = raw.get("body", {})
        return body.get("content", "") or ""
    return ""


def _extract_received_at(provider: str, raw: dict) -> datetime | None:
    if provider == "gmail":
        headers = raw.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name") == "Date":
                try:
                    return _parse_datetime(h.get("value", ""))
                except Exception:
                    pass
        return None
    if provider == "outlook":
        try:
            return _parse_datetime(raw.get("receivedDateTime", ""))
        except Exception:
            return None
    return None


def _parse_datetime(s: str) -> datetime:
    """Parse ISO8601 or RFC2822 datetime string."""
    s = s.strip()
    if not s:
        raise ValueError("empty")
    # Try ISO format first
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    # Try email date format (RFC 2822)
    from email.utils import parsedate_to_datetime
    return parsedate_to_datetime(s)


def _extract_is_read(provider: str, raw: dict) -> bool:
    if provider == "gmail":
        return "UNREAD" not in raw.get("labelIds", [])
    if provider == "outlook":
        return raw.get("isRead", False)
    return False


def _extract_attachments(provider: str, raw: dict) -> str | None:
    """Extract attachment metadata as a JSON string or None.
    Decision: store metadata (filename, mime_type, size_bytes) only.
    Do NOT index or summarize attachment content in MVP."""
    items: list[dict] = []
    if provider == "gmail":

        def _walk_parts(part_list: list[dict]):
            for part in part_list:
                if part.get("filename"):
                    items.append({
                        "filename": part["filename"],
                        "mime_type": part.get("mimeType", "application/octet-stream"),
                        "size_bytes": part.get("body", {}).get("size", 0),
                    })
                if "parts" in part:
                    _walk_parts(part["parts"])

        _walk_parts(raw.get("payload", {}).get("parts", []))
    elif provider == "outlook":
        for att in (raw.get("attachments") or []):
            if isinstance(att, dict):
                items.append({
                    "filename": att.get("name", "unnamed"),
                    "mime_type": att.get("contentType", "application/octet-stream"),
                    "size_bytes": att.get("size", 0),
                })
    return json.dumps(items) if items else None
