"""Reads the account header and transaction rows from a passbook page.

A transaction row starts with its date; a second date on the same row is the value date and
is dropped. Amount cells are read from the end of the row: the last is the running balance,
the one before it is the transaction. Whether that transaction is a debit comes from the
Dr/Cr printed beside its cell, then from the balance change, then from the column it sits
under, then from the narration wording.
"""

import re
from dataclasses import dataclass
from datetime import date

from app.domain.models import TxnChannel
from app.infra.extractors.ocr import OcrLine, OcrPage, OcrWord
from app.infra.extractors.parsers.common import (
    DATE_PATTERN,
    ParseResult,
    cash_marker,
    clean_name,
    completeness,
    find_value,
    fix_numeric_page,
    normalize_digits,
    parse_amount_cell,
    parse_date,
    value_after,
)
from app.schemas.document import PassbookFields, Transaction

_HOLDER = re.compile(
    r"(?<![A-Za-z])(?:a/?c\.?\s*holder(?:'?s)?\s*name|customer\s*name|account\s*holder|name|नाम)"
    r"(?!\s*of\s*branch)(?![\u0900-\u097F])",
    re.I,
)
_NOT_HOLDER = re.compile(r"branch|nominee|नामांकित|father|husband|bank", re.I)
# OCR often reads the c in "A/c" as e.
_ACCOUNT = re.compile(r"(?:a\s*/?\s*[ce]\.?|account|खाता)\s*(?:(?:no|number|num)\.?|संख्या)?", re.I)
_ACCOUNT_NUMBER = re.compile(r"[\dX*][\dX*\s-]{5,}")
# Shorter runs are dates and phone numbers printed in the same header block.
_MIN_ACCOUNT_DIGITS = 9
_IFSC = re.compile(r"\b([A-Z]{4})[0O]([A-Z0-9]{6})\b")
_BRANCH = re.compile(r"branch(?:\s*name)?|शाखा", re.I)
_NOMINEE = re.compile(r"nominee(?:\s*name)?|नामांकित", re.I)
_NO_NOMINEE = re.compile(r"^(?:not\s*registered|nil|none|no|n\.?a\.?|-+)$", re.I)
_OPENING = re.compile(
    r"b/?f\b|brought\s*forward|opening\s*bal|balance\s*b|carried\s*forward|c/?f\b|"
    r"पिछला\s*शेष|शेष\s*आगे",
    re.I,
)
_CREDIT_WORDS = re.compile(
    r"^\s*by\b|\bcr\b|credit|deposit|\bdep\b|interest|neft\s*cr|refund|reversal", re.I
)
_DEBIT_HEADERS = re.compile(r"withdraw|debit|^dr\.?$", re.I)
_CREDIT_HEADERS = re.compile(r"deposit|credit|^cr\.?$", re.I)
# A repeated page header or label: never the wrapped half of a narration.
_HEADER_LINE = re.compile(
    r"ifsc|micr|branch|शाखा|statement|account|खाता|नाम(?![\u0900-\u097F])|\bname\b|page\s*\d|"
    r"particulars|state\s+bank|punjab\s+national|bank\s+of|canara|union\s+bank|india\s+post|"
    r"brought\s+forward|carried\s+forward|continued",
    re.I,
)
_NUMBERISH = re.compile(r"^[\d,.]+$")
_PIPE = "|"
# Only the transaction amount and the running balance are ever used from a row.
_MAX_CELLS = 2
# "28 May 2026" reaches the parser as three words; numeric dates as one.
_DATE_TAKES = (1, 2, 3)

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
    "IPOS": "India Post",
}
BANKS_BY_NAME = {
    "STATE BANK OF INDIA": "SBI",
    "PUNJAB NATIONAL BANK": "PNB",
    "BANK OF BARODA": "Bank of Baroda",
    "CANARA BANK": "Canara Bank",
    "UNION BANK OF INDIA": "Union Bank of India",
    "BANK OF INDIA": "Bank of India",
    "INDIA POST": "India Post",
}


@dataclass(frozen=True)
class _Cell:
    amount: int
    marker: str | None
    """The Dr/Cr the bank printed with this cell, if it did."""
    center: float
    """x-centre of the word it was read from."""


@dataclass
class _Row:
    day: date
    narration: str
    cells: tuple[_Cell, ...]


def _strip_pipes(page: OcrPage) -> OcrPage:
    """Drops the column rules OCR reads as '|', which otherwise split amounts in half."""
    lines = []
    for line in page.lines:
        words = tuple(
            OcrWord(text, w.confidence, w.left, w.width)
            for w in line.words
            if (text := w.text.strip(_PIPE))
        )
        lines.append(OcrLine(words))
    return OcrPage(tuple(lines))


def _is_one_space(a: OcrWord, b: OcrWord) -> bool:
    char = a.width / max(len(a.text), 1)
    return 0 <= b.left - (a.left + a.width) <= 1.5 * char


def _splits_number(a: OcrWord, b: OcrWord) -> bool:
    """True when OCR put a space inside one amount ("4 36.00" for 436.00)."""
    if not (_NUMBERISH.match(a.text) and _NUMBERISH.match(b.text)):
        return False
    # Without a dot the halves are two amounts, not one, so never glue those back together.
    if "." not in a.text + b.text or not _is_one_space(a, b):
        return False
    return parse_amount_cell(a.text + b.text) is not None


def _merge_split_numbers(words: list[OcrWord]) -> list[OcrWord]:
    merged: list[OcrWord] = []
    for word in words:
        if merged and _splits_number(merged[-1], word):
            half = merged.pop()
            merged.append(
                OcrWord(
                    half.text + word.text,
                    min(half.confidence, word.confidence),
                    half.left,
                    word.left + word.width - half.left,
                )
            )
        else:
            merged.append(word)
    return merged


def _one_date(words: list[OcrWord]) -> tuple[date | None, int]:
    for take in _DATE_TAKES:
        if take > len(words):
            break
        text = " ".join(w.text for w in words[:take])
        match = DATE_PATTERN.match(text)
        if match and match.end() == len(text) and (day := parse_date(text)):
            return day, take
    return None, 0


def _dates_from(words: list[OcrWord], start: int) -> tuple[date | None, int]:
    day, taken = None, start
    for _ in range(2):
        found, used = _one_date(words[taken:])
        if found is None:
            break
        day = day or found
        taken += used
    return day, taken


def _leading_date(words: list[OcrWord]) -> tuple[date | None, int]:
    """The day a row starts with and how many words the date, or both dates, take up.

    A serial-number column prints a short number in front of the date, so a row that only
    starts with a date once that number is stepped over is accepted too.
    """
    day, taken = _dates_from(words, 0)
    if day is not None:
        return day, taken
    if words and re.fullmatch(r"\d{1,3}", words[0].text):
        return _dates_from(words, 1)
    return None, 0


def _scan_cells(words: list[OcrWord]) -> tuple[tuple[_Cell, ...], list[OcrWord]]:
    """The amount cells at the end of a row, and the narration words in front of them."""
    cells: list[_Cell] = []
    marker: str | None = None
    index = len(words)
    while index > 0 and len(cells) < _MAX_CELLS:
        text = words[index - 1].text
        cell = parse_amount_cell(text)
        if cell is not None:
            amount, own = cell
            cells.insert(0, _Cell(amount, own or marker, words[index - 1].center))
            marker, index = None, index - 1
            continue
        lone = cash_marker(text)
        if lone is not None and index > 1 and parse_amount_cell(words[index - 2].text):
            marker, index = lone, index - 1
            continue
        break
    return tuple(cells), words[:index]


def _narration(words: list[OcrWord]) -> str:
    text = " ".join(w.text for w in words).replace(_PIPE, " ")
    return re.sub(r"\s+", " ", text).strip()


def _columns_line(text: str) -> bool:
    return bool(_DEBIT_HEADERS.search(text) and _CREDIT_HEADERS.search(text))


def _is_noise(text: str) -> bool:
    if _columns_line(text):
        return True
    if not re.search(r"[A-Za-z\u0900-\u097F]", text):
        return True
    return bool(_HEADER_LINE.search(text))


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
        words = _merge_split_numbers(list(line.words))
        day, taken = _leading_date(words)
        if day is not None:
            cells, narration = _scan_cells(words[taken:])
            rows.append(_Row(day, _narration(narration), cells))
            continue
        cells, narration = _scan_cells(words)
        wrapped = _narration(narration)
        # Long narrations wrap onto a second line with no date and no amounts of their own.
        if rows and not cells and wrapped and not _is_noise(line.text):
            rows[-1].narration = f"{rows[-1].narration} {wrapped}".strip()
    return rows


def _repair_missing_paise(amount: int, balance: int, previous: int) -> int:
    """OCR drops the decimal point, so a cell reads 43600 where the row only moved 436."""
    moved = abs(balance - previous)
    return moved if moved and amount == moved * 100 else amount


def _is_debit(
    cell: _Cell,
    amount: int,
    balance: int | None,
    previous: int | None,
    columns: tuple[float | None, float | None],
    narration: str,
) -> bool:
    if cell.marker is not None:
        return cell.marker == "dr"
    if balance is not None and previous is not None and abs(balance - previous) == amount:
        return balance < previous
    debit_x, credit_x = columns
    if debit_x is not None and credit_x is not None:
        return abs(cell.center - debit_x) < abs(cell.center - credit_x)
    return not _CREDIT_WORDS.search(narration)


def _transactions(page: OcrPage) -> list[Transaction]:
    columns = _columns(page)
    txns: list[Transaction] = []
    previous: int | None = None
    for row in _rows(fix_numeric_page(page)):
        if _OPENING.search(row.narration):
            if row.cells:
                previous = row.cells[-1].amount
            continue
        if not row.cells:
            continue
        cell = row.cells[-2] if len(row.cells) > 1 else row.cells[-1]
        balance = row.cells[-1].amount if len(row.cells) > 1 else None
        amount = cell.amount
        if balance is not None and previous is not None:
            amount = _repair_missing_paise(amount, balance, previous)
        debit = _is_debit(cell, amount, balance, previous, columns, row.narration)
        txns.append(
            Transaction(
                date=row.day,
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
        name = clean_name(value_after(line.text, _HOLDER))
        if name:
            return name
    return None


def _account_last4(page: OcrPage) -> str | None:
    for line in page.lines:
        raw = value_after(line.text, _ACCOUNT)
        number = _ACCOUNT_NUMBER.search(normalize_digits(raw or "").upper())
        if not number:
            continue
        digits = re.sub(r"[^\dX*]", "", number.group())
        if len(digits) >= _MIN_ACCOUNT_DIGITS and re.fullmatch(r"\d{4}", digits[-4:]):
            return digits[-4:]
    return None


def _ifsc(page: OcrPage) -> str | None:
    for line in page.lines:
        match = _IFSC.search(line.text.upper())
        if match:
            return f"{match.group(1)}0{match.group(2)}"
    return None


def _bank(page: OcrPage, ifsc: str | None) -> str | None:
    if ifsc and ifsc[:4] in BANKS_BY_IFSC:
        return BANKS_BY_IFSC[ifsc[:4]]
    # Longest name first: "UNION BANK OF INDIA" also contains "BANK OF INDIA".
    for line in page.lines[:8]:
        for name in sorted(BANKS_BY_NAME, key=len, reverse=True):
            if name in line.text.upper():
                return BANKS_BY_NAME[name]
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
    page = _strip_pipes(page)
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
