"""Spam detection: rule-based signals + sender reputation from user feedback."""
from __future__ import annotations

import json
import re
from email.utils import parseaddr
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import ClassificationFeedback, Email


# -- Signal: keyword matching (existing rules) --

SPAM_KEYWORDS = [
    "lottery", "winner", "prize", "click here", "free money",
    "congratulations", "you won", "claim your", "act now",
    "limited time", "exclusive offer", "100% free", "risk free",
    "no obligation", "special promotion", "once in a lifetime",
    "guaranteed", "credit card", "social security number",
    "bank account details", "money back", "cash bonus",
]


def _keyword_signal(text: str) -> list[str]:
    t = text.lower()
    return [f"keyword:{w}" for w in SPAM_KEYWORDS if w in t]


# -- Signal: link detection --

URL_PATTERN = re.compile(r"https?://[^\s]+")

SUSPICIOUS_TLDS = {".xyz", ".top", ".loan", ".work", ".click", ".pw", ".buzz", ".gq", ".ml", ".ga"}


def _link_signals(text: str) -> list[str]:
    urls = URL_PATTERN.findall(text)
    signals = []
    for url in urls:
        for tld in SUSPICIOUS_TLDS:
            if tld in url:
                signals.append(f"link:suspicious_tld:{tld}")
    if len(urls) > 5:
        signals.append(f"link:excessive_links:{len(urls)}")
    return signals


# -- Signal: all-caps ratio --

def _allcaps_signal(text: str) -> list[str]:
    words = [w for w in text.split() if len(w) > 1]
    if not words:
        return []
    caps = sum(1 for w in words if w.isupper())
    ratio = caps / len(words)
    if ratio > 0.3:
        return [f"allcaps:ratio:{ratio:.2f}"]
    return []


# -- Signal: exclamation density --

def _exclamation_signal(text: str) -> list[str]:
    count = text.count("!")
    if count >= 3:
        return [f"exclamation:{count}"]
    return []


# -- Signal: suspicious sender patterns --

def _normalize_sender(sender: str) -> str:
    """Extract addr from 'Name <addr@domain>' format."""
    _, addr = parseaddr(sender)
    return addr.lower() if addr else sender.lower()


def _sender_signal(sender: str) -> list[str]:
    signals = []
    addr = _normalize_sender(sender)
    if any(w in addr for w in ["noreply", "no-reply", "donotreply"]):
        signals.append("sender:noreply")
    if re.search(r"\d{5,}", addr):
        signals.append("sender:numeric_pattern")
    if "@" in addr and re.search(r"\.(xyz|top|loan|click|pw|buzz)$", addr):
        signals.append("sender:suspicious_domain")
    return signals


# -- Signal: sender reputation from user feedback --

def _reputation_signal(db: Session, user_id: int, sender: str) -> list[str]:
    """Check classification_feedback for user's past spam reports against this sender."""
    addr = _normalize_sender(sender)
    domain = ""
    if "@" in addr:
        domain = addr.split("@")[-1]

    if domain:
        total_from_domain = (
            db.query(Email)
            .filter(
                Email.user_id == user_id,
                Email.sender.ilike(f"%@{domain}%"),
            )
            .count()
        )
        if total_from_domain > 0:
            spam_from_domain = (
                db.query(ClassificationFeedback)
                .join(Email, ClassificationFeedback.email_id == Email.id)
                .filter(
                    ClassificationFeedback.user_id == user_id,
                    ClassificationFeedback.new_category == "spam",
                    Email.sender.ilike(f"%@{domain}%"),
                )
                .count()
            )
            domain_spam_ratio = spam_from_domain / total_from_domain
            if domain_spam_ratio > 0.5:
                return [f"reputation:domain_blocked:{domain}"]
            elif domain_spam_ratio > 0.2:
                return [f"reputation:domain_suspicious:{domain}"]
    return []


# -- Main detection function --

def detect_spam(
    db: Session, user_id: int, email: dict
) -> tuple[float, list[str]]:
    """Return (spam_confidence 0-1, list of signal names)."""
    subject = email.get("subject", "")
    body = email.get("body", "")
    sender = email.get("sender", "")
    text = f"{subject} {body}"

    signals: list[str] = []
    signals += _keyword_signal(text)
    signals += _link_signals(text)
    signals += _allcaps_signal(body)
    signals += _exclamation_signal(text)
    signals += _sender_signal(sender)
    signals += _reputation_signal(db, user_id, sender)

    # Score: each keyword/link/reputation signal = 0.15, caps/exclamation = 0.05
    score = 0.0
    for s in signals:
        if s.startswith("keyword:") or s.startswith("link:") or s.startswith("reputation:"):
            score += 0.15
        elif s.startswith("sender:"):
            score += 0.1
        else:
            score += 0.08

    return min(1.0, score), signals
