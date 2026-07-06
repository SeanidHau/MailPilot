from enum import Enum


class EmailCategory(str, Enum):
    important = "important"
    normal = "normal"
    promotion = "promotion"
    bill = "bill"
    school_work = "school_work"
    needs_reply = "needs_reply"
    spam = "spam"


class DraftTone(str, Enum):
    formal = "formal"
    brief = "brief"
    polite_decline = "polite_decline"
    ask_info = "ask_info"


class ReminderType(str, Enum):
    deadline = "deadline"
    meeting = "meeting"
    payment = "payment"
    reply_task = "reply_task"
    other = "other"


class ReminderStatus(str, Enum):
    pending = "pending"
    done = "done"
    deleted = "deleted"


class DraftStatus(str, Enum):
    draft = "draft"
    saved = "saved"
