"""
Mock AI provider regression tests — validate rule-based classification accuracy,
reminder extraction precision, reply draft quality, and summarization coverage.

These tests target MockAIProvider specifically and do NOT cover real LLM providers.
For OpenAI/Anthropic evaluation, run with real API keys and a separate eval harness.
"""
from app.ai.providers.mock import MockAIProvider


# ---- Ground truth dataset ----

GROUND_TRUTH = [
    {"subject": "Q3 Budget Review - Action Required",
     "body": "Please review the Q3 budget proposal. Deadline: 2026-07-15. This is urgent - please respond by end of week.",
     "expected_category": "important", "has_deadline": True, "has_reply": True},
    {"subject": "FLASH SALE: 50% Off All Software Licenses!",
     "body": "Limited time offer! Click to claim your discount. Unsubscribe here.",
     "expected_category": "promotion", "has_deadline": False, "has_reply": False},
    {"subject": "Your Monthly Subscription Invoice",
     "body": "Your monthly subscription has been processed. Amount: $14.99.",
     "expected_category": "bill", "has_deadline": False, "has_reply": False},
    {"subject": "CS 401 Project Report Due Next Week",
     "body": "Semester project reports are due on 2026-07-12. Submit through the portal.",
     "expected_category": "school_work", "has_deadline": True, "has_reply": False},
    {"subject": "Interview Follow-up: Senior Developer Position",
     "body": "Please confirm your availability for a second interview. Respond within 48 hours.",
     "expected_category": "needs_reply", "has_deadline": False, "has_reply": True},
    {"subject": "CONGRATULATIONS! You Won $5,000,000!!!",
     "body": "You won the lottery sweepstakes! Reply with your bank details to claim.",
     "expected_category": "spam", "has_deadline": False, "has_reply": False},
    {"subject": "Sprint planning tomorrow at 10am",
     "body": "Sprint planning tomorrow. Please come prepared. Zoom link attached.",
     "expected_category": "normal", "has_deadline": False, "has_reply": False},
    {"subject": "Invoice #INV-2026-0789 Due Payment",
     "body": "Invoice #INV-2026-0789 for $2,350.00 is due by 2026-07-20. Pay online.",
     "expected_category": "bill", "has_deadline": True, "has_reply": False},
]

provider = MockAIProvider()


# ---- Classification accuracy ----

def test_classify_all_correct_categories():
    """Every email in the ground truth set must classify to its expected category."""
    for item in GROUND_TRUTH:
        category, score, error = provider.classify_email(item)
        assert category == item["expected_category"], \
            f"'{item['subject'][:40]}' classified as '{category}', expected '{item['expected_category']}'"


def test_classification_accuracy_rate():
    """Overall classification accuracy should be 100% for this curated set."""
    correct = 0
    for item in GROUND_TRUTH:
        category, _, _ = provider.classify_email(item)
        if category == item["expected_category"]:
            correct += 1
    accuracy = correct / len(GROUND_TRUTH)
    assert accuracy == 1.0, f"Classification accuracy: {accuracy:.1%}"


def test_importance_score_range():
    """All importance scores must be in 1-5 range."""
    for item in GROUND_TRUTH:
        _, score, _ = provider.classify_email(item)
        assert 1 <= score <= 5, f"Score {score} out of range for '{item['subject'][:40]}'"


def test_important_emails_score_highest():
    """Important emails must score >= 4."""
    for item in GROUND_TRUTH:
        if item["expected_category"] == "important":
            _, score, _ = provider.classify_email(item)
            assert score >= 4, f"Important email scored only {score}: '{item['subject'][:40]}'"


def test_spam_scores_lowest():
    """Spam emails must score <= 2."""
    for item in GROUND_TRUTH:
        if item["expected_category"] == "spam":
            _, score, _ = provider.classify_email(item)
            assert score <= 2, f"Spam email scored {score}: '{item['subject'][:40]}'"


# ---- Reminder extraction quality ----

def test_extract_reminders_for_deadline_emails():
    """Emails with deadlines should generate reminders."""
    for item in GROUND_TRUTH:
        if item["has_deadline"]:
            reminders, error = provider.extract_reminders(item)
            assert len(reminders) >= 1, \
                f"No reminders extracted from deadline email: '{item['subject'][:40]}'"


def test_extract_reminders_for_reply_needs():
    """Emails needing reply should generate reply_task reminders."""
    for item in GROUND_TRUTH:
        if item["has_reply"]:
            reminders, error = provider.extract_reminders(item)
            types = [r["reminder_type"] for r in reminders]
            assert "reply_task" in types, \
                f"No reply_task reminder for: '{item['subject'][:40]}'"


def test_no_false_reminders_for_promotion():
    """Promotional emails should not generate deadline or payment reminders."""
    reminders, error = provider.extract_reminders(GROUND_TRUTH[1])  # FLASH SALE
    types = [r["reminder_type"] for r in reminders]
    assert "deadline" not in types
    assert "payment" not in types


def test_no_match_generates_followup_reminder():
    """Mock provider generates a fallback 'other' follow-up when no keywords match.
    This differs from the LLM prompt which expects []; the mock behavior is
    intentionally more aggressive to surface every email as actionable."""
    email = {"subject": "Just a hello", "body": "Nothing urgent here. Just checking in."}
    reminders, error = provider.extract_reminders(email)
    assert len(reminders) >= 1
    assert reminders[0]["reminder_type"] == "other"
    assert "follow" in reminders[0]["title"].lower()


def test_extract_reminders_returns_error_none():
    """Mock provider always returns error=None."""
    for item in GROUND_TRUTH:
        _, error = provider.extract_reminders(item)
        assert error is None


def test_reminder_title_not_empty():
    """Every reminder must have a non-empty title."""
    for item in GROUND_TRUTH:
        reminders, error = provider.extract_reminders(item)
        for r in reminders:
            assert r["title"], f"Empty reminder title for: '{item['subject'][:40]}'"


def test_date_extraction_accuracy():
    """Dates in YYYY-MM-DD format should be extracted to due_at field."""
    email = {"subject": "Deadline", "body": "Submit by 2026-12-31."}
    reminders, _ = provider.extract_reminders(email)
    assert len(reminders) >= 1
    assert "2026-12-31" in reminders[0].get("due_at", "")


# ---- Reply draft quality ----

def test_draft_contains_sender_name():
    """Draft must reference the original sender."""
    for tone in ("formal", "brief", "polite_decline", "ask_info"):
        content, error = provider.generate_reply({"sender": "Alice", "subject": "Hello"}, tone)
        assert "Alice" in content, f"{tone} draft missing sender name"


def test_draft_not_empty():
    """Every draft tone must produce non-empty content."""
    for tone in ("formal", "brief", "polite_decline", "ask_info"):
        content, error = provider.generate_reply({"sender": "Bob", "subject": "Test"}, tone)
        assert len(content) > 10, f"{tone} draft too short: {content}"


def test_fallback_tone():
    """Unknown tone should fallback to formal."""
    content, error = provider.generate_reply({"sender": "X", "subject": "Y"}, "nonexistent")
    assert len(content) > 10
    assert error is None


def test_draft_error_is_none():
    """Mock provider always returns error=None for drafts."""
    for tone in ("formal", "brief", "polite_decline", "ask_info"):
        _, error = provider.generate_reply({"sender": "A", "subject": "B"}, tone)
        assert error is None


# ---- Summarization quality ----

def test_summary_non_empty():
    """Every summary must be non-empty."""
    for item in GROUND_TRUTH:
        summary, error = provider.summarize_email(item)
        assert len(summary) > 0, f"Empty summary for: '{item['subject'][:40]}'"


def test_long_email_summary_shorter_than_body():
    """Summary must be shorter than the original body."""
    long_email = {"subject": "Long", "body": "A. " * 100}
    summary, _ = provider.summarize_email(long_email)
    assert len(summary) < len(long_email["body"])


def test_short_email_summary_handled():
    """Very short emails should still produce a summary."""
    summary, _ = provider.summarize_email({"subject": "Hi", "body": "Thanks."})
    assert len(summary) > 0


# ---- Edge cases ----

def test_empty_email_fields():
    """Provider handles empty subject/body gracefully."""
    category, score, error = provider.classify_email({"subject": "", "body": ""})
    assert category == "normal"
    assert 1 <= score <= 5


def test_missing_fields():
    """Provider handles missing keys gracefully with safe defaults."""
    category, score, error = provider.classify_email({})
    assert category == "normal"
    assert 1 <= score <= 5
    assert error is None
