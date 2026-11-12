"""Rolling one-hour preparation limits (DEC-134)."""

from exam_photo.api.protection import RateLimiter


def test_a_key_may_go_until_the_limit_then_waits():
    limiter = RateLimiter(3)
    for i in range(3):
        assert limiter.retry_after("kit_a", now=1000.0 + i) == 0
        limiter.record("kit_a", now=1000.0 + i)
    wait = limiter.retry_after("kit_a", now=1010.0)
    assert 3500 < wait <= 3600


def test_the_window_rolls():
    limiter = RateLimiter(1)
    limiter.record("kit_a", now=0.0)
    assert limiter.retry_after("kit_a", now=1800.0) > 0
    assert limiter.retry_after("kit_a", now=3601.0) == 0


def test_keys_are_independent_and_zero_switches_it_off():
    limiter = RateLimiter(1)
    limiter.record("kit_a", now=0.0)
    assert limiter.retry_after("kit_b", now=1.0) == 0
    off = RateLimiter(0)
    off.record("kit_a", now=0.0)
    assert off.retry_after("kit_a", now=1.0) == 0
    assert limiter.retry_after(None, now=1.0) == 0
