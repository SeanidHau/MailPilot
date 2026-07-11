import json
from app.ai.spam import detect_spam, _keyword_signal, _link_signals, _allcaps_signal, _exclamation_signal, _sender_signal


class TestSpamSignals:
    def test_keyword_detection(self):
        signals = _keyword_signal("You won the lottery! Claim your prize now!")
        assert len(signals) >= 2  # lottery, prize, you won, claim your

    def test_link_suspicious_tld(self):
        signals = _link_signals("Check this out: http://free.xyz/money and http://spam.top/win")
        assert any("xyz" in s for s in signals)
        assert any("top" in s for s in signals)

    def test_link_excessive(self):
        text = " ".join([f"http://link{i}.com" for i in range(10)])
        signals = _link_signals(text)
        assert any("excessive" in s for s in signals)

    def test_allcaps_ratio(self):
        signals = _allcaps_signal("THIS IS VERY IMPORTANT please read this")
        # "THIS" "IS" "VERY" "IMPORTANT" are caps, "please" "read" "this" are not = 4/7 ~ 0.57
        assert any("allcaps" in s for s in signals)

    def test_exclamation_density(self):
        signals = _exclamation_signal("First sentence with auto-reply!!! Second sentence also! Third with wow!!")
        assert len(signals) >= 1

    def test_sender_noreply(self):
        signals = _sender_signal("noreply@spam.xyz")
        assert "sender:noreply" in signals
        assert "sender:suspicious_domain" in signals

    def test_sender_numeric_pattern(self):
        signals = _sender_signal("user123456@example.com")
        assert "sender:numeric_pattern" in signals


class TestSpamDetection:
    def test_clean_email_scores_low(self, db_session):
        email = {"subject": "Meeting tomorrow", "body": "Hi team, let's meet at 10am to discuss the project.", "sender": "alice@company.com"}
        confidence, signals = detect_spam(db_session, user_id=1, email=email)
        assert confidence < 0.3
        assert isinstance(signals, list)

    def test_spam_email_scores_high(self, db_session):
        email = {
            "subject": "YOU WON THE LOTTERY!!!",
            "body": "Congratulations! You won $5,000,000! Click here to claim your prize: http://win.xyz/money. Act now!",
            "sender": "noreply@prizes.xyz",
        }
        confidence, signals = detect_spam(db_session, user_id=1, email=email)
        assert confidence > 0.5
        assert len(signals) >= 3

    def test_spam_stored_on_classify(self, auth_client, db_session):
        """Classify endpoint stores spam_confidence and spam_signals."""
        auth_client.post("/api/emails/import")
        auth_client.post("/api/emails/6/classify")  # email 6 = lottery spam
        from app.db.models import Email
        email = db_session.query(Email).filter(Email.id == 6).first()
        assert email.spam_confidence is not None
        assert email.spam_confidence >= 0
        if email.spam_signals:
            signals = json.loads(email.spam_signals)
            assert isinstance(signals, list)

    def test_spam_confidence_range(self, db_session):
        """spam_confidence always in 0-1 range."""
        emails = [
            {"subject": "Hi", "body": "Just checking in", "sender": "friend@example.com"},
            {"subject": "WINNER!!!", "body": "Claim your prize at spam.xyz. Act now!", "sender": "noreply@spam.top"},
        ]
        for e in emails:
            confidence, _ = detect_spam(db_session, user_id=1, email=e)
            assert 0.0 <= confidence <= 1.0
