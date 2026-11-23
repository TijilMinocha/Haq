from dataclasses import replace

import pytest

from app.domain.facts import CaseFacts
from app.domain.models import CoverStatus, EventType, TxnChannel
from app.domain.rules import rupay

from .factories import CONFIG, TODAY, atm, claim, d, passbook, protect, txn


@pytest.mark.parametrize(
    ("facts", "status", "amount", "reason"),
    [
        pytest.param(
            claim(passbook=passbook(card_bin=None)),
            CoverStatus.NOT_FOUND,
            0,
            "no_rupay_card",
            id="no-card",
        ),
        pytest.param(
            claim(passbook=passbook(atm("2026-10-30"), card_bin="411111")),
            CoverStatus.INELIGIBLE,
            0,
            "card_not_eligible",
            id="not-rupay-bin",
        ),
        pytest.param(
            claim(atm("2026-10-30")),
            CoverStatus.LIKELY_ELIGIBLE,
            200000,
            "card_txn_within_lookback",
            id="atm-in-window",
        ),
        pytest.param(
            claim(passbook=passbook(atm("2026-10-30"), card_issued_on=d("2016-01-01"))),
            CoverStatus.LIKELY_ELIGIBLE,
            100000,
            "card_txn_within_lookback",
            id="old-card",
        ),
        pytest.param(
            claim(atm("2026-10-30"), event=EventType.NATURAL_DEATH),
            CoverStatus.INELIGIBLE,
            0,
            "accident_only_cover",
            id="natural-death",
        ),
        pytest.param(
            claim(atm("2026-08-01")),
            CoverStatus.INELIGIBLE,
            0,
            "no_card_txn_in_window",
            id="atm-too-old",
        ),
        pytest.param(
            claim(atm("2026-10-30"), event=None),
            CoverStatus.NEEDS_VERIFICATION,
            200000,
            "event_details_missing",
            id="no-event",
        ),
    ],
)
def test_cover_status(facts: CaseFacts, status: CoverStatus, amount: int, reason: str) -> None:
    cover = rupay.evaluate(facts, CONFIG).cover
    assert (cover.status, cover.amount) == (status, amount)
    assert cover.reasons[0].code == reason


def test_window_is_90_days_inclusive() -> None:
    assert rupay.evaluate(claim(atm("2026-08-17")), CONFIG).cover.status is (
        CoverStatus.LIKELY_ELIGIBLE
    )
    assert rupay.evaluate(claim(atm("2026-08-16")), CONFIG).cover.status is CoverStatus.INELIGIBLE


def test_no_recent_txn_flag() -> None:
    result = rupay.evaluate(claim(atm("2026-01-01")), CONFIG)
    assert [f.code for f in result.flags] == ["rupay_no_recent_txn"]


def test_upi_only_needs_bank_verification() -> None:
    facts = claim(txn("2026-11-01", "UPI/P2P/RAMU", 500), atm("2026-01-01"))
    result = rupay.evaluate(facts, CONFIG)
    assert result.cover.status is CoverStatus.NEEDS_VERIFICATION
    assert [f.code for f in result.flags] == ["rupay_txn_unverifiable"]


def test_extractor_channel_counts() -> None:
    facts = claim(txn("2026-11-01", "WDL", 500, channel=TxnChannel.MICRO_ATM))
    assert rupay.evaluate(facts, CONFIG).cover.status is CoverStatus.LIKELY_ELIGIBLE


def test_intimation_deadline_is_hard_90_days() -> None:
    (deadline,) = rupay.evaluate(claim(atm("2026-10-30")), CONFIG).deadlines
    assert (deadline.code, deadline.due_date, deadline.hard) == (
        "claim_intimation",
        d("2027-02-13"),
        True,
    )


@pytest.mark.parametrize(
    ("last_use", "status", "alert", "days_left"),
    [
        ("2026-09-06", CoverStatus.ELIGIBLE, "alert.rupay_expiring", 12),
        ("2026-11-20", CoverStatus.ELIGIBLE, "alert.cover_active", None),
        ("2026-07-01", CoverStatus.LAPSED, "alert.cover_lapsed", None),
    ],
)
def test_protect_window(
    last_use: str, status: CoverStatus, alert: str, days_left: int | None
) -> None:
    result = rupay.evaluate(protect(atm(last_use)), CONFIG)
    assert result.cover.status is status
    assert result.alerts[0].code == alert
    if days_left is not None:
        assert result.alerts[0].params["days_left"] == days_left


def test_protect_ignores_future_card_use() -> None:
    facts = replace(protect(atm("2026-12-30")), today=TODAY)
    assert rupay.evaluate(facts, CONFIG).cover.status is CoverStatus.LAPSED
