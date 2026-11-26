import pytest

from app.domain.config.loader import PremiumScheme
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


@pytest.mark.parametrize(
    ("narration", "expected"),
    [
        pytest.param("CASH DEPOSIT BY RAJU", TxnChannel.OTHER, id="deposit-is-not-pos"),
        pytest.param("POSTAGE CHG", TxnChannel.OTHER, id="postage-is-not-pos"),
        pytest.param("BATMAN STORE PURCHASE", TxnChannel.OTHER, id="batman-is-not-atm"),
        pytest.param("CSPL CHARGES", TxnChannel.OTHER, id="cspl-is-not-bc"),
        pytest.param("ATM WDL SEELAMPUR", TxnChannel.ATM, id="atm"),
        pytest.param("NFS/ATM/123", TxnChannel.ATM, id="nfs-atm"),
        pytest.param("POS 4521 BIG BAZAAR", TxnChannel.POS, id="pos"),
        pytest.param("PRCH 8842 METRO", TxnChannel.POS, id="purchase"),
        pytest.param("MATM CASH WDL", TxnChannel.MICRO_ATM, id="matm"),
        pytest.param("MICRO ATM CASH WDL", TxnChannel.MICRO_ATM, id="micro-atm"),
        pytest.param("UPI/1234/PAYTM", TxnChannel.UPI, id="upi"),
        pytest.param("AEPS WDL", TxnChannel.AEPS, id="aeps"),
        pytest.param("BC/CSP WDL", TxnChannel.BC, id="bc"),
        pytest.param("ECOM AMAZON", TxnChannel.ECOM, id="ecom"),
    ],
)
def test_channel_matches_only_on_token_boundaries(narration: str, expected: TxnChannel) -> None:
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
    ("narration", "amount", "scheme", "expected"),
    [
        pytest.param("SBY 2026 PREMIUM", 20, CONFIG.pmsby, True, id="sby-alone"),
        pytest.param("JJBY PREMIUM", 436, CONFIG.pmjjby, True, id="jjby-alone"),
        pytest.param("SBYTES NEFT CHG", 20, CONFIG.pmsby, False, id="sby-inside-a-word"),
        pytest.param("PASSBYTE RETURN", 20, CONFIG.pmsby, False, id="sby-inside-passbook"),
        pytest.param("RAJJBY TRANSFER", 436, CONFIG.pmjjby, False, id="jjby-inside-a-word"),
    ],
)
def test_premium_patterns_match_only_on_token_boundaries(
    narration: str, amount: int, scheme: PremiumScheme, expected: bool
) -> None:
    assert is_premium(txn("2026-05-28", narration, amount), scheme) is expected


@pytest.mark.parametrize("amount", [342, 228, 114])
def test_pro_rata_pmjjby_premiums_are_recognised(amount: int) -> None:
    assert amount in CONFIG.pmjjby.premium_amounts
    assert is_premium(txn("2026-09-01", "PMJJBY PREMIUM", amount), CONFIG.pmjjby)


def test_pmjjby_premium_one_rupee_off_is_not_recognised() -> None:
    assert is_premium(txn("2026-09-01", "PMJJBY PREMIUM", 435), CONFIG.pmjjby) is False


@pytest.mark.parametrize("narration", ["PMJJBY REFUND", "PMJJBY REVERSAL", "PMJJBY CR"])
def test_a_credit_is_never_a_premium(narration: str) -> None:
    assert is_premium(txn("2026-05-28", narration, 436, debit=False), CONFIG.pmjjby) is False


@pytest.mark.parametrize(("amount", "expected"), [(20, True), (436, False)])
def test_pmsby_premium_is_twenty_rupees(amount: int, expected: bool) -> None:
    assert is_premium(txn("2026-05-30", "PMSBY PREMIUM", amount), CONFIG.pmsby) is expected


@pytest.mark.parametrize(
    ("day", "year"),
    [("2026-05-31", 2025), ("2026-06-01", 2026), ("2026-12-31", 2026), ("2027-01-15", 2026)],
)
def test_cover_year_starts_in_june(day: str, year: int) -> None:
    assert cover_year_of(d(day), CONFIG.cover_year_start) == year


@pytest.mark.parametrize(
    ("debit", "year"),
    [
        ("2026-05-24", 2025),  # the day before the window pays for the year that is ending
        ("2026-05-28", 2026),  # renewal window pays for the coming year
        ("2026-05-10", 2025),  # mid-year enrolment before the window
        ("2026-06-20", 2026),
        ("2027-02-01", 2026),
    ],
)
def test_year_paid_by(debit: str, year: int) -> None:
    assert year_paid_by(d(debit), CONFIG.pmjjby, CONFIG.cover_year_start) == year
