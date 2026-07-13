from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Email, Reminder


def get_dashboard_summary(db: Session, user_id: int):
    email_q = db.query(Email).filter(Email.user_id == user_id, Email.is_deleted.is_(False))
    reminder_q = db.query(Reminder).filter(Reminder.user_id == user_id)

    total_emails = email_q.count()
    pending_emails = email_q.filter(Email.is_read == False).count()
    important_emails = email_q.filter(Email.importance_score >= 4).count()
    pending_reminders = reminder_q.filter(Reminder.status == "pending").count()

    recent_important = (
        email_q.filter(Email.importance_score >= 4)
        .order_by(Email.received_at.desc())
        .limit(5).all()
    )
    recent_important_data = [
        {
            "id": e.id, "sender": e.sender, "subject": e.subject,
            "category": e.category, "importance_score": e.importance_score,
            "received_at": e.received_at.isoformat() if e.received_at else None,
        }
        for e in recent_important
    ]

    upcoming_reminders = (
        reminder_q.filter(Reminder.status == "pending")
        .order_by(Reminder.due_at.asc().nullslast())
        .limit(5).all()
    )
    upcoming_data = [
        {
            "id": r.id, "title": r.title, "reminder_type": r.reminder_type,
            "due_at": r.due_at.isoformat() if r.due_at else None,
            "email_subject": r.email.subject if r.email else "",
        }
        for r in upcoming_reminders
    ]

    return {
        "total_emails": total_emails,
        "pending_emails": pending_emails,
        "important_emails": important_emails,
        "pending_reminders": pending_reminders,
        "recent_important_emails": recent_important_data,
        "upcoming_reminders": upcoming_data,
    }
