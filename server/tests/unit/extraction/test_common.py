import re
from datetime import date

import pytest

from app.infra.extractors.parsers.common import (
    clean_name,
    fix_numeric_word,
    parse_amount,
    parse_amount_cell,
    parse_date,
    value_after,
)

from .passbook_corpus import devanagari

_NAME_LABEL = re.compile(r"name|नाम(?![\u0900-\u097F])", re.I)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("28-05-2026", date(2026, 5, 28)),
        ("28/05/26", date(2026, 5, 28)),
        ("on 2.6.2026 at", date(2026, 6, 2)),
        ("15 Nov 2026", date(2026, 11, 15)),
        ("15-NOVEMBER-2026", date(2026, 11, 15)),
        ("31-02-2026 then 01-03-2026", date(2026, 3, 1)),
        ("२८-०५-२०२६", date(2026, 5, 28)),
        ("no date here", None),
    ],
)
def test_parse_date(text: str, expected: date | None) -> None:
    assert parse_date(text) == expected


def test_parse_amount_rounds_paise() -> None:
    assert parse_amount("4,564.00") == 4564
    assert parse_amount("1,00,000.50") == 100000
    assert parse_amount(devanagari("436.00")) == 436


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("436.00", (436, None)),
        ("436", (436, None)),
        ("1,23,456.00", (123456, None)),
        ("4,564.00Cr", (4564, "cr")),
        ("436.00DR.", (436, "dr")),
        ("(20.00)", (20, None)),
        ("436.00 Dr", None),
        ("202600000001234567", None),
        ("PMJJBY", None),
    ],
)
def test_parse_amount_cell(text: str, expected: tuple[int, str | None] | None) -> None:
    assert parse_amount_cell(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("OI-O5-2O26", "01-05-2026"),
        ("2B-O5-2O26", "28-05-2026"),
        ("06~09-2026", "06-09-2026"),
        ("4S6.OO", "456.00"),
        ("SBIN0001234", "SBIN0001234"),
        ("UPI/P2M/998877665544/KIRANA", "UPI/P2M/998877665544/KIRANA"),
    ],
)
def test_fix_numeric_word_only_rewrites_words_that_then_read_as_numbers(
    text: str, expected: str
) -> None:
    assert fix_numeric_word(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Name : RAMESH KUMAR", "RAMESH KUMAR"),
        ("नाम / Name : RAMESH KUMAR", "RAMESH KUMAR"),
        ("Name of Account Holder : RAMESH KUMAR", "RAMESH KUMAR"),
        ("नामांकित : सुनीता देवी", None),
    ],
)
def test_value_after_drops_the_label_of_the_other_language(text: str, expected: str | None) -> None:
    assert value_after(text, _NAME_LABEL) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("RAMESH KUMAR", "Ramesh Kumar"),
        ("RAMESH KUMAR Nominee: SUNITA", "Ramesh Kumar"),
        ("RAMESH KUMAR 4417", "Ramesh Kumar"),
        ("रमेश कुमार", "रमेश कुमार"),
        ("", None),
    ],
)
def test_clean_name(raw: str, expected: str | None) -> None:
    assert clean_name(raw) == expected
