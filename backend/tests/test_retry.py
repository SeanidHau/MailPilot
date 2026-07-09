import time
import pytest
from app.ai.retry import is_retryable, RateLimiter


class FakeStatusError(Exception):
    def __init__(self, msg, status_code):
        super().__init__(msg)
        self.status_code = status_code


def test_is_retryable_429():
    assert is_retryable(FakeStatusError("rate limited", 429))


def test_is_retryable_5xx():
    for code in (500, 502, 503, 504):
        assert is_retryable(FakeStatusError("server error", code))


def test_is_not_retryable_400():
    assert not is_retryable(FakeStatusError("bad request", 400))


def test_is_not_retryable_401():
    assert not is_retryable(FakeStatusError("unauthorized", 401))


def test_is_retryable_timeout_message():
    assert is_retryable(Exception("Connection timeout"))


def test_is_retryable_rate_limit_message():
    assert is_retryable(Exception("Too many requests"))


def test_is_not_retryable_other():
    assert not is_retryable(Exception("something else"))


def test_rate_limiter_allows_first_call():
    rl = RateLimiter(1000)
    start = time.monotonic()
    rl.acquire()
    assert time.monotonic() - start < 0.1


def test_rate_limiter_throttles():
    rl = RateLimiter(120)  # 2 per second = 0.5s interval
    start = time.monotonic()
    rl.acquire()
    rl.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.4  # should have waited ~0.5s


def test_with_retry_succeeds_first_try():
    from app.ai.retry import with_retry
    result = with_retry(lambda: "ok", "test")
    assert result == "ok"


def test_with_retry_eventually_succeeds():
    from app.ai.retry import with_retry
    call_count = [0]

    def flaky():
        call_count[0] += 1
        if call_count[0] < 2:
            raise FakeStatusError("server error", 503)
        return "recovered"

    result = with_retry(flaky, "test")
    assert result == "recovered"
    assert call_count[0] == 2


def test_with_retry_fails_after_exhaustion():
    from app.ai.retry import with_retry

    with pytest.raises(FakeStatusError):
        with_retry(lambda: (_ for _ in ()).throw(FakeStatusError("server error", 503)), "test")
