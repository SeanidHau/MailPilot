from app.ai.providers.mock import MockAIProvider


def test_classify_important():
    provider = MockAIProvider()
    email = {"subject": "URGENT: Deadline approaching", "body": "Action required immediately. This is critical."}
    category, score = provider.classify_email(email)
    assert category == "important"
    assert score >= 4


def test_classify_promotion():
    provider = MockAIProvider()
    email = {"subject": "50% discount sale!", "body": "Limited time offer. Unsubscribe at any time."}
    category, score = provider.classify_email(email)
    assert category == "promotion"
    assert score == 2


def test_classify_spam():
    provider = MockAIProvider()
    email = {"subject": "You won the lottery!", "body": "Congratulations! You are a prize winner. Click here."}
    category, score = provider.classify_email(email)
    assert category == "spam"
    assert score == 1


def test_classify_bill():
    provider = MockAIProvider()
    email = {"subject": "Your invoice is ready", "body": "Please process the payment for your subscription."}
    category, score = provider.classify_email(email)
    assert category == "bill"
    assert score == 3


def test_classify_school_work():
    provider = MockAIProvider()
    email = {"subject": "Assignment due next week", "body": "Please submit your project report to the professor."}
    category, score = provider.classify_email(email)
    assert category == "school_work"
    assert score == 3


def test_classify_needs_reply():
    provider = MockAIProvider()
    email = {"subject": "Can you confirm?", "body": "Please respond with your feedback on this question."}
    category, score = provider.classify_email(email)
    assert category == "needs_reply"
    assert score == 3


def test_classify_normal():
    provider = MockAIProvider()
    email = {"subject": "Hello", "body": "Just saying hi and checking in. Hope you are well."}
    category, score = provider.classify_email(email)
    assert category == "normal"
    assert 1 <= score <= 5


def test_summarize_email():
    provider = MockAIProvider()
    email = {"subject": "Project update", "body": "The project is on track. We completed phase one. The next milestone is next month. Please review the attached report."}
    summary = provider.summarize_email(email)
    assert "project" in summary.lower()
    assert len(summary) > 0


def test_summarize_short_email():
    provider = MockAIProvider()
    email = {"subject": "Hi", "body": "Thanks."}
    summary = provider.summarize_email(email)
    assert len(summary) > 0


def test_generate_reply_formal():
    provider = MockAIProvider()
    email = {"sender": "boss@corp.com", "subject": "Q3 Report"}
    reply = provider.generate_reply(email, "formal")
    assert "boss@corp.com" in reply
    assert "Q3 Report" in reply


def test_generate_reply_brief():
    provider = MockAIProvider()
    email = {"sender": "colleague@corp.com", "subject": "Lunch?"}
    reply = provider.generate_reply(email, "brief")
    assert "colleague@corp.com" in reply


def test_extract_reminders_deadline():
    provider = MockAIProvider()
    email = {"subject": "Project deadline", "body": "The deadline for submission is 2026-07-15. Please complete by this due date."}
    reminders = provider.extract_reminders(email)
    assert len(reminders) >= 1
    assert reminders[0]["reminder_type"] == "deadline"


def test_extract_reminders_meeting():
    provider = MockAIProvider()
    email = {"subject": "Sprint planning", "body": "We have a meeting via Zoom tomorrow. Calendar invite attached."}
    reminders = provider.extract_reminders(email)
    assert any(r["reminder_type"] == "meeting" for r in reminders)


def test_extract_reminders_fallback():
    provider = MockAIProvider()
    email = {"subject": "Hello", "body": "Just a friendly note. Nothing urgent."}
    reminders = provider.extract_reminders(email)
    assert len(reminders) >= 1
    assert reminders[0]["reminder_type"] == "other"
