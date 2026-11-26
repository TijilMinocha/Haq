from dataclasses import replace
from datetime import timedelta

import pytest

from app.domain.facts import CaseFacts
from app.domain.models import CoverStatus, EventType, TxnChannel
from app.domain.rules import rupay

from .factories import CONFIG, EVENT, TODAY, atm, claim, d, passbook, protect, txn


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


@pytest.mark.parametrize(
    ("days_before", "status"),
    [
        pytest.param(CONFIG.rupay.txn_lookback_days - 1, CoverStatus.LIKELY_ELIGIBLE, id="89-days"),
        pytest.param(CONFIG.rupay.txn_lookback_days, CoverStatus.LIKELY_ELIGIBLE, id="90-days"),
        pytest.param(CONFIG.rupay.txn_lookback_days + 1, CoverStatus.INELIGIBLE, id="91-days"),
        pytest.param(0, CoverStatus.LIKELY_ELIGIBLE, id="on-the-event-day"),
    ],
)
def test_lookback_window_boundary(days_before: int, status: CoverStatus) -> None:
    facts = claim(atm(EVENT - timedelta(days=days_before)))
    assert rupay.evaluate(facts, CONFIG).cover.status is status


def test_card_use_after_the_event_does_not_count() -> None:
    cover = rupay.evaluate(claim(atm(EVENT + timedelta(days=1))), CONFIG).cover
    assert cover.status is CoverStatus.INELIGIBLE
    assert cover.reasons[0].code == "no_card_txn_in_window"


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


CARD_USE: dict[TxnChannel, str] = {
    TxnChannel.ATM: "ATM WDL SEELAMPUR",
    TxnChannel.MICRO_ATM: "MATM CASH WDL",
    TxnChannel.POS: "POS 4521 BIG BAZAAR",
    TxnChannel.ECOM: "ECOM AMAZON",
    TxnChannel.BC: "BC/CSP WDL",
    TxnChannel.UPI: "UPI/1234/PAYTM",
    TxnChannel.AEPS: "AEPS WDL",
}


def test_the_narrations_cover_every_configured_channel() -> None:
    assert set(CARD_USE) == CONFIG.rupay.counting_channels | CONFIG.rupay.unverifiable_channels


@pytest.mark.parametrize(("channel", "narration"), list(CARD_USE.items()))
def test_only_card_channels_prove_the_card_was_used(channel: TxnChannel, narration: str) -> None:
    counted = channel in CONFIG.rupay.counting_channels
    expected = CoverStatus.LIKELY_ELIGIBLE if counted else CoverStatus.NEEDS_VERIFICATION
    result = rupay.evaluate(claim(txn("2026-11-01", narration, 500)), CONFIG)
    assert result.cover.status is expected


@pytest.mark.parametrize(
    ("offset", "reason", "amount"),
    [
        pytest.param(-1, "old_card_amount", CONFIG.rupay.old_card_amount, id="day-before"),
        pytest.param(0, "old_card_amount", CONFIG.rupay.old_card_amount, id="on-the-cutoff"),
        pytest.param(1, "new_card_amount", CONFIG.rupay.new_card_amount, id="day-after"),
    ],
)
def test_card_issue_date_decides_the_sum_insured(offset: int, reason: str, amount: int) -> None:
    issued = CONFIG.rupay.new_card_after + timedelta(days=offset)
    pb = passbook(atm("2026-10-30"), card_issued_on=issued)
    cover = rupay.evaluate(claim(passbook=pb), CONFIG).cover
    assert (cover.amount, cover.reasons[-1].code) == (amount, reason)


def test_unknown_issue_date_assumes_the_old_amount() -> None:
    pb = passbook(atm("2026-10-30"), card_issued_on=None)
    cover = rupay.evaluate(claim(passbook=pb), CONFIG).cover
    assert (cover.amount, cover.reasons[-1].code) == (
        CONFIG.rupay.old_card_amount,
        "card_issue_date_unknown",
    )


def test_a_refund_does_not_count_as_card_use() -> None:
    refund = txn("2026-11-01", "POS REFUND BIG BAZAAR", 650, debit=False)
    result = rupay.evaluate(claim(refund), CONFIG)
    assert result.cover.status is CoverStatus.INELIGIBLE
    assert result.cover.reasons[0].code == "no_card_txn_in_window"
    assert rupay.evaluate(protect(refund), CONFIG).cover.status is CoverStatus.LAPSED


def test_intimation_deadline_is_hard_90_days() -> None:
    (deadline,) = rupay.evaluate(claim(atm("2026-10-30")), CONFIG).deadlines
    assert (deadline.code, deadline.due_date, deadline.hard) == (
        "claim_intimation",
        d("2027-02-13"),
        True,
    )


@pytest.mark.parametrize(
    ("days_left", "status", "alert"),
    [
        pytest.param(
            CONFIG.rupay.expiry_warning_days + 1, CoverStatus.ELIGIBLE, "alert.cover_active"
        ),
        pytest.param(
            CONFIG.rupay.expiry_warning_days, CoverStatus.ELIGIBLE, "alert.rupay_expiring"
        ),
        pytest.param(0, CoverStatus.ELIGIBLE, "alert.rupay_expiring"),
        pytest.param(-1, CoverStatus.LAPSED, "alert.cover_lapsed"),
    ],
)
def test_protect_expiry_boundary(days_left: int, status: CoverStatus, alert: str) -> None:
    last_use = TODAY + timedelta(days=days_left - CONFIG.rupay.txn_lookback_days)
    result = rupay.evaluate(protect(atm(last_use)), CONFIG)
    assert result.cover.status is status
    assert result.alerts[0].code == alert
    # Only the warning carries the countdown: "active" is deliberately param-free.
    if alert == "alert.rupay_expiring":
        assert result.alerts[0].params["days_left"] == days_left


def test_protect_ignores_future_card_use() -> None:
    facts = replace(protect(atm("2026-12-30")), today=TODAY)
    assert rupay.evaluate(facts, CONFIG).cover.status is CoverStatus.LAPSED
