from app.infra.extractors.parsers import passbook
from app.schemas.document import PassbookFields

from .helpers import expected, page

SUNITA = """
STATE BANK OF INDIA
Branch: SEELAMPUR IFSC: SBIN0001234
Name: RAMESH KUMAR
A/c No: 00000031234564417
Nominee: SUNITA DEVI
Date Particulars Withdrawal Deposit Balance
01-05-2026 BALANCE B/F 5,000.00
28-05-2026 PMJJBY PREMIUM 436.00 4,564.00
30-05-2026 PMSBY PREMIUM 20.00 4,544.00
02-10-2026 BY CASH 3,000.00 7,544.00
30-10-2026 ATM WDL SEELAMPUR 2,000.00 5,544.00
"""


def _parse(text: str) -> PassbookFields:
    fields = passbook.parse(page(text)).fields
    assert isinstance(fields, PassbookFields)
    return fields


def test_reads_the_sunita_passbook() -> None:
    result = passbook.parse(page(SUNITA))
    want = PassbookFields.model_validate(expected("sunita_passbook")["fields"])
    assert result.fields == want
    assert result.completeness == 1.0


def test_direction_falls_back_to_narration_without_balances() -> None:
    fields = _parse(
        """
        12-01-2026 BY CLG NEFT CR 1,500.00
        13-01-2026 TO ATM WDL 500.00
        """
    )
    assert [t.direction for t in fields.transactions] == ["credit", "debit"]


def test_direction_uses_columns_when_first_row_has_no_previous_balance() -> None:
    fields = _parse(
        """
        Date      Particulars       Withdrawal  Deposit    Balance
        05-01-2026 SALARY MAY                   9,000.00   9,000.00
        """
    )
    assert fields.transactions[0].direction == "credit"


def test_wrapped_narration_joins_the_row_above() -> None:
    fields = _parse(
        """
        01-05-2026 BALANCE B/F 1,000.00
        28-05-2026 PMJJBY 436.00 564.00
        PREMIUM AUTO DEBIT
        """
    )
    assert fields.transactions[0].narration == "PMJJBY PREMIUM AUTO DEBIT"


def test_nominee_not_registered_is_none() -> None:
    assert _parse("Nominee: NOT REGISTERED").nominee_name is None


def test_masked_account_still_gives_last_four() -> None:
    assert _parse("Account Number: XXXX-XXXX-9021").account_last4 == "9021"


def test_ifsc_with_letter_o_is_corrected_and_names_the_bank() -> None:
    fields = _parse("IFSC: PUNBO123400")
    assert (fields.ifsc, fields.bank) == ("PUNB0123400", "PNB")


def test_empty_page_has_zero_completeness() -> None:
    assert passbook.parse(page("hello world")).completeness == 0


def test_tolerates_common_ocr_slips() -> None:
    fields = _parse(
        """
        A/e No: 0123 00XX XXXX 9021
        01-06-2026 BALANCE B/F 2,000.00
        06~09-2026 POS KIRANA STORE 650.00 1,350.00
        O2-1l-2026 UPI/P2P/RAMU 5OO.00 850.00
        """
    )
    assert fields.account_last4 == "9021"
    assert [(t.date.isoformat(), t.amount) for t in fields.transactions] == [
        ("2026-09-06", 650),
        ("2026-11-02", 500),
    ]
