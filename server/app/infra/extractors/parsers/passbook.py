"""Reads the account header and transaction rows from a passbook page.

Rows are recognised by a leading date. The last amount on a row is the running balance;
the one before it is the transaction. Whether it is a debit or a credit comes from the
balance change, then from the column it sits under, then from the narration wording.
"""

import re
from dataclasses import dataclass

from app.domain.models import TxnChannel
from app.infra.extractors.ocr import OcrLine, OcrPage
from app.infra.extractors.parsers.common import (
    AMOUNT_PATTERN,
    DATE_PATTERN,
    ParseResult,
    clean_name,
    completeness,
    find_value,
    fix_numeric_page,
    parse_amount,
    parse_date,
)
from app.schemas.document import PassbookFields, Transaction

_HOLDER = re.compile(
    r"(?<![A-Za-z])(?:a/?c\.?\s*holder(?:'?s)?\s*name|customer\s*name|name|नाम)(?!\s*of\s*branch)",
    re.I,
)
_NOT_HOLDER = re.compile(r"branch|nominee|father|husband|bank", re.I)
# OCR often reads the c in "A/c" as e.
_ACCOUNT = re.compile(r"(?:a\s*/?\s*[ce]\.?|account)\s*(?:no|number|num)\.?", re.I)
_ACCOUNT_NUMBER = re.compile(r"[\dX*][\dX*\s-]{5,}")
_IFSC = re.compile(r"\b([A-Z]{4})[0O]([A-Z0-9]{6})\b")
_BRANCH = re.compile(r"branch(?:\s*name)?", re.I)
_NOMINEE = re.compile(r"nominee(?:\s*name)?|नामांकित", re.I)
_NO_NOMINEE = re.compile(r"^(?:not\s*registered|nil|none|no|n\.?a\.?|-+)$", re.I)
_OPENING = re.compile(r"b/f|brought\s*forward|opening\s*bal|balance\s*b", re.I)
_CREDIT_WORDS = re.compile(
    r"^\s*by\b|\bcr\b|credit|deposit|\bdep\b|interest|neft\s*cr|refund", re.I
)
_DEBIT_HEADERS = re.compile(r"withdraw|debit|^dr\.?$", re.I)
_CREDIT_HEADERS = re.compile(r"deposit|credit|^cr\.?$", re.I)

BANKS_BY_IFSC = {
    "SBIN": "SBI",
    "PUNB": "PNB",
    "BARB": "Bank of Baroda",
    "CNRB": "Canara Bank",
    "UBIN": "Union Bank of India",
    "BKID": "Bank of India",
    "IOBA": "Indian Overseas Bank",
    "UCBA": "UCO Bank",
    "CBIN": "Central Bank of India",
    "IDIB": "Indian Bank",
    "MAHB": "Bank of Maharashtra",
    "PSIB": "Punjab & Sind Bank",
}
BANKS_BY_NAME = {
    "STATE BANK OF INDIA": "SBI",
    "PUNJAB NATIONAL BANK": "PNB",
    "BANK OF BARODA": "Bank of Baroda",
    "CANARA BANK": "Canara Bank",
}


@dataclass
class _Row:
    line: OcrLine
    narration: str
    amounts: list[tuple[int, float]]
    """Each amount with the x-centre of the word it was read from."""


def _amount_positions(line: OcrLine) -> list[tuple[int, float]]:
    found = []
    for word in line.words:
        for match in AMOUNT_PATTERN.finditer(word.text):
            found.append((parse_amount(match.group()), word.center))
    return found


def _columns(page: OcrPage) -> tuple[float | None, float | None]:
    """x-centres of the withdrawal and deposit headers, if a header row was read."""
    for line in page.lines:
        debit = next((w.center for w in line.words if _DEBIT_HEADERS.search(w.text)), None)
        credit = next((w.center for w in line.words if _CREDIT_HEADERS.search(w.text)), None)
        if debit is not None and credit is not None:
            return debit, credit
    return None, None


def _rows(page: OcrPage) -> list[_Row]:
    rows: list[_Row] = []
    for line in page.lines:
        text = line.text
        date_match = DATE_PATTERN.match(text.strip())
        if date_match:
            rest = text.strip()[date_match.end() :]
            first_amount = AMOUNT_PATTERN.search(rest)
            narration = rest[: first_amount.start()] if first_amount else rest
            rows.append(_Row(line, narration.strip(" |"), _amount_positions(line)))
        elif rows and not AMOUNT_PATTERN.search(text) and not _columns_line(text):
            # Long narrations wrap onto a second line with no date or amounts.
            rows[-1].narration = f"{rows[-1].narration} {text.strip(' |')}".strip()
    return rows


def _columns_line(text: str) -> bool:
    return bool(_DEBIT_HEADERS.search(text) and _CREDIT_HEADERS.search(text))


def _is_debit(
    row: _Row,
    amount: int,
    amount_x: float,
    balance: int | None,
    previous: int | None,
    columns: tuple[float | None, float | None],
) -> bool:
    if balance is not None and previous is not None and abs(balance - previous) == amount:
        return balance < previous
    debit_x, credit_x = columns
    if debit_x is not None and credit_x is not None:
        return abs(amount_x - debit_x) < abs(amount_x - credit_x)
    return not _CREDIT_WORDS.search(row.narration)


def _transactions(page: OcrPage) -> list[Transaction]:
    columns = _columns(page)
    txns, previous = [], None
    for row in _rows(fix_numeric_page(page)):
        day = parse_date(row.line.text)
        if day is None or not row.amounts:
            continue
        if _OPENING.search(row.narration):
            previous = row.amounts[-1][0]
            continue
        if len(row.amounts) >= 2:
            (amount, amount_x), balance = row.amounts[-2], row.amounts[-1][0]
        else:
            (amount, amount_x), balance = row.amounts[-1], None
        debit = _is_debit(row, amount, amount_x, balance, previous, columns)
        txns.append(
            Transaction(
                date=day,
                narration=row.narration or "-",
                amount=amount,
                direction="debit" if debit else "credit",
                channel=TxnChannel.OTHER,
            )
        )
        if balance is not None:
            previous = balance
    return txns


def _holder(page: OcrPage) -> str | None:
    for line in page.lines:
        if _NOT_HOLDER.search(line.text.split(":")[0]):
            continue
        name = clean_name(find_value(OcrPage((line,)), _HOLDER))
        if name:
            return name
    return None


def _account_last4(page: OcrPage) -> str | None:
    raw = find_value(page, _ACCOUNT)
    if not raw:
        return None
    number = _ACCOUNT_NUMBER.search(raw.upper())
    if not number:
        return None
    digits = re.sub(r"[^\dX*]", "", number.group())
    return digits[-4:] if re.fullmatch(r"\d{4}", digits[-4:]) else None


def _ifsc(page: OcrPage) -> str | None:
    for line in page.lines:
        match = _IFSC.search(line.text.upper())
        if match:
            return f"{match.group(1)}0{match.group(2)}"
    return None


def _bank(page: OcrPage, ifsc: str | None) -> str | None:
    if ifsc and ifsc[:4] in BANKS_BY_IFSC:
        return BANKS_BY_IFSC[ifsc[:4]]
    for line in page.lines[:8]:
        for name, short in BANKS_BY_NAME.items():
            if name in line.text.upper():
                return short
    return None


def _nominee(page: OcrPage) -> str | None:
    value = find_value(page, _NOMINEE)
    if not value or _NO_NOMINEE.match(value.strip()):
        return None
    return clean_name(value) or value.strip()


def _branch(page: OcrPage) -> str | None:
    value = find_value(page, _BRANCH)
    if not value:
        return None
    return re.split(r"\s{2,}|\bIFSC\b", value, flags=re.I)[0].strip(" :") or None


def parse(page: OcrPage) -> ParseResult:
    ifsc = _ifsc(page)
    fields = PassbookFields(
        account_holder=_holder(page),
        bank=_bank(page, ifsc),
        branch=_branch(page),
        ifsc=ifsc,
        account_last4=_account_last4(page),
        nominee_name=_nominee(page),
        transactions=_transactions(page),
    )
    # Transactions carry the insurance evidence, so they weigh as much as the header.
    score = 0.5 * completeness(fields.account_holder, fields.account_last4) + 0.5 * (
        1.0 if fields.transactions else 0.0
    )
    return ParseResult(fields, score)
