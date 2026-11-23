from datetime import date

import pytest

from app.infra.extractors.parsers.common import clean_name, parse_amount, parse_date


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("28-05-2026", date(2026, 5, 28)),
        ("28/05/26", date(2026, 5, 28)),
        ("on 2.6.2026 at", date(2026, 6, 2)),
        ("15 Nov 2026", date(2026, 11, 15)),
        ("15-NOVEMBER-2026", date(2026, 11, 15)),
        ("31-02-2026 then 01-03-2026", date(2026, 3, 1)),
        ("no date here", None),
    ],
)
def test_parse_date(text: str, expected: date | None) -> None:
    assert parse_date(text) == expected


def test_parse_amount_rounds_paise() -> None:
    assert parse_amount("4,564.00") == 4564
    assert parse_amount("1,00,000.50") == 100000


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
