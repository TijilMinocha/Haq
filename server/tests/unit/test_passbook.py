import pytest

from app.domain.models import TxnChannel
from app.domain.passbook import channel_of, cover_year_of, is_premium, year_paid_by

from .factories import CONFIG, d, txn


@pytest.mark.parametrize(
    ("narration", "expected"),
    [
        ("ATM WDL SEELAMPUR", TxnChannel.ATM),
        ("MICRO ATM CASH WDL", TxnChannel.MICRO_ATM),
        ("UPI/P2M/KIRANA", TxnChannel.UPI),
        ("AEPS CASH WDL", TxnChannel.AEPS),
        ("POS KIRANA STORE", TxnChannel.POS),
        ("BC/CSP CASH", TxnChannel.BC),
        ("BY CASH", TxnChannel.OTHER),
    ],
)
def test_channel_inferred_from_narration(narration: str, expected: TxnChannel) -> None:
    assert channel_of(txn("2026-10-01", narration, 100), CONFIG) is expected


def test_extractor_channel_wins_over_narration() -> None:
    assert channel_of(txn("2026-10-01", "UPI", 1, channel=TxnChannel.POS), CONFIG) is TxnChannel.POS


@pytest.mark.parametrize(
    ("narration", "amount", "debit", "expected"),
    [
        ("PMJJBY PREMIUM", 436, True, True),
        ("JEEVAN JYOTI BIMA", 436, True, True),
        ("PMJJBY PREMIUM", 342, True, True),
        ("PMJJBY PREMIUM", 500, True, False),
        ("PMJJBY REFUND", 436, False, False),
        ("PMSBY PREMIUM", 436, True, False),
    ],
)
def test_pmjjby_premium_needs_pattern_amount_and_debit(
    narration: str, amount: int, debit: bool, expected: bool
) -> None:
    assert is_premium(txn("2026-05-28", narration, amount, debit=debit), CONFIG.pmjjby) is expected


@pytest.mark.parametrize(
    ("day", "year"),
    [("2026-05-31", 2025), ("2026-06-01", 2026), ("2026-12-31", 2026), ("2027-01-15", 2026)],
)
def test_cover_year_starts_in_june(day: str, year: int) -> None:
    assert cover_year_of(d(day), CONFIG.cover_year_start) == year


@pytest.mark.parametrize(
    ("debit", "year"),
    [
        ("2026-05-28", 2026),  # renewal window pays for the coming year
        ("2026-05-10", 2025),  # mid-year enrolment before the window
        ("2026-06-20", 2026),
        ("2027-02-01", 2026),
    ],
)
def test_year_paid_by(debit: str, year: int) -> None:
    assert year_paid_by(d(debit), CONFIG.pmjjby, CONFIG.cover_year_start) == year
