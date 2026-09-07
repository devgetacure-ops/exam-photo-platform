"""Protecting capacity, and measuring what it is used for (DEC-073).

Preparation is ten seconds of CPU and free until someone buys. The threat is
not the money -- a hundred photographs cost a rupee of a VPS already paid for
-- it is availability on a deadline day, which is the same as sales.

What is pinned here is mostly the shape of the trade: the allowance is off by
default and stops a candidate only when configured, a purchase clears it, and
the challenge fails **open** where the payment secrets fail shut.
"""

from datetime import datetime, timezone

import pytest

from exam_photo.api.protection import (
    AllowanceExceededError,
    ChallengeFailedError,
    KitUsage,
    UsageRegistry,
    verify_turnstile,
)

KIT = "kit_abuse"


@pytest.fixture
def usage(tmp_path):
    return UsageRegistry(tmp_path / "artifacts")


# ----------------------------------------------------------------------
# Counters
# ----------------------------------------------------------------------


def test_preparations_are_counted_per_kit(usage):
    for _ in range(3):
        usage.record_preparation(KIT)

    record = usage.get(KIT)
    assert record.preparations == 3
    assert record.preparations_since_purchase == 3


def test_counters_survive_the_jobs_they_describe(usage, tmp_path):
    """Retention erases the jobs every thirty minutes. A counter that went
    with them would reset the allowance twice an hour, which is no allowance."""
    usage.record_preparation(KIT)

    reopened = UsageRegistry(tmp_path / "artifacts")

    assert reopened.get(KIT).preparations == 1


def test_an_unknown_kit_has_no_counters(usage):
    assert usage.get("kit_never_seen") is None


def test_a_malformed_kit_id_is_not_read_from_disk(usage):
    assert usage.get("../../escape") is None


# ----------------------------------------------------------------------
# The allowance
# ----------------------------------------------------------------------


def test_the_allowance_is_off_by_default(usage):
    """DEC-073 turns it on only once the counters say what is normal."""
    for _ in range(100):
        usage.record_preparation(KIT)

    usage.check_allowance(KIT, 0)  # must not raise


def test_the_allowance_stops_a_kit_that_never_buys(usage):
    for _ in range(5):
        usage.record_preparation(KIT)

    with pytest.raises(AllowanceExceededError) as caught:
        usage.check_allowance(KIT, 5)

    assert caught.value.used == 5 and caught.value.allowance == 5


def test_a_purchase_clears_the_allowance(usage):
    """A paying candidate is never stopped: the limit bounds free use."""
    for _ in range(5):
        usage.record_preparation(KIT)
    usage.record_purchase(KIT)

    usage.check_allowance(KIT, 5)  # must not raise
    record = usage.get(KIT)
    assert record.preparations == 5
    assert record.preparations_since_purchase == 0
    assert record.purchases == 1


def test_the_lifetime_count_is_kept_across_purchases(usage):
    usage.record_preparation(KIT)
    usage.record_purchase(KIT)
    usage.record_preparation(KIT)

    assert usage.get(KIT).preparations == 2


def test_a_kit_that_has_done_nothing_is_never_refused(usage):
    usage.check_allowance("kit_fresh", 1)  # must not raise


# ----------------------------------------------------------------------
# The challenge, which fails open on purpose
# ----------------------------------------------------------------------


def test_no_secret_means_no_challenge():
    verify_turnstile("", "", None)  # must not raise


def test_a_configured_challenge_needs_a_token():
    with pytest.raises(ChallengeFailedError, match="no challenge token"):
        verify_turnstile("", "a-secret", None)


def test_a_rejected_token_is_refused(monkeypatch):
    import httpx

    class Response:
        def json(self):
            return {"success": False, "error-codes": ["invalid-input-response"]}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Response())

    with pytest.raises(ChallengeFailedError, match="rejected"):
        verify_turnstile("a-token", "a-secret", None)


def test_an_accepted_token_passes(monkeypatch):
    import httpx

    class Response:
        def json(self):
            return {"success": True}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Response())

    verify_turnstile("a-token", "a-secret", None)  # must not raise


def test_cloudflare_being_down_does_not_take_the_product_down(monkeypatch):
    """The deliberate asymmetry: the payment secrets fail shut, this fails open.

    An unverified webhook releases files nobody paid for. An unchallenged
    preparation costs a fraction of a rupee. Refusing every candidate because
    a third party is unreachable is the more expensive mistake.
    """
    import httpx

    def explode(*args, **kwargs):
        raise httpx.ConnectError("cloudflare unreachable")

    monkeypatch.setattr(httpx, "post", explode)

    verify_turnstile("a-token", "a-secret", None)  # must not raise


# ----------------------------------------------------------------------
# The summary that should decide the allowance
# ----------------------------------------------------------------------


def test_an_empty_service_summarises_to_nothing(usage):
    summary = usage.summary()

    assert summary["kits"] == 0
    assert summary["conversion_rate"] is None


def test_the_summary_reports_a_distribution_not_just_a_mean(usage):
    """One script and a thousand candidates have a mean describing neither."""
    now = datetime.now(timezone.utc).isoformat()
    for index in range(20):
        usage._save(
            KitUsage(
                kit_id=f"kit_{index:03d}",
                preparations=2,
                purchases=1 if index < 5 else 0,
                first_seen=now,
                last_seen=now,
            )
        )
    usage._save(
        KitUsage(
            kit_id="kit_script",
            preparations=900,
            purchases=0,
            first_seen=now,
            last_seen=now,
        )
    )

    summary = usage.summary()

    assert summary["kits"] == 21
    assert summary["preparations"] == 940
    assert summary["preparations_per_kit"]["median"] == 2
    assert summary["preparations_per_kit"]["max"] == 900
    assert summary["kits_that_purchased"] == 5


def test_the_summary_names_the_heaviest_kits(usage):
    now = datetime.now(timezone.utc).isoformat()
    usage._save(
        KitUsage(kit_id="kit_light", preparations=1, first_seen=now, last_seen=now)
    )
    usage._save(
        KitUsage(kit_id="kit_heavy", preparations=500, first_seen=now, last_seen=now)
    )

    heaviest = usage.summary()["heaviest_kits"]

    assert heaviest[0]["kit_id"] == "kit_heavy"
    assert heaviest[0]["preparations"] == 500


def test_a_corrupt_counter_file_does_not_break_the_summary(usage):
    usage.record_preparation(KIT)
    (usage.root / "kit_broken.json").write_text("{not json", encoding="utf-8")

    assert usage.summary()["kits"] == 1
