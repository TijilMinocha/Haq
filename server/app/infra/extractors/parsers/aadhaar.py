"""Aadhaar front side: name, date of birth, gender and the masked number.

The number is masked in the OCR text before this parser ever sees it.
"""

import re

from app.infra.extractors.ocr import OcrPage
from app.infra.extractors.parsers.common import ParseResult, clean_name, completeness, parse_date
from app.schemas.document import IdentityFields

_DOB = re.compile(r"dob|date\s*of\s*birth|जन्म\s*तिथि|year\s*of\s*birth", re.I)
_MASKED = re.compile(r"XXXX-XXXX-(\d{4})")
_GENDER = {"MALE": "male", "FEMALE": "female", "पुरुष": "male", "महिला": "female"}
_NOT_NAME = re.compile(r"government|india|भारत|सरकार|aadhaar|आधार|dob|address|पता|vid", re.I)
_LATIN_NAME = re.compile(r"^[A-Za-z][A-Za-z .]{2,}$")


def _name(lines: list[str], dob_index: int | None) -> str | None:
    # The English name sits just above the DOB line; the Hindi name is above that.
    candidates = lines[:dob_index] if dob_index is not None else lines
    for text in reversed(candidates):
        if _LATIN_NAME.match(text.strip()) and not _NOT_NAME.search(text):
            return clean_name(text)
    return None


def parse(page: OcrPage) -> ParseResult:
    lines = [line.text for line in page.lines]
    dob_index = next((i for i, t in enumerate(lines) if _DOB.search(t)), None)
    dob = parse_date(lines[dob_index]) if dob_index is not None else None
    gender = next(
        (g for t in lines for word, g in _GENDER.items() if re.search(rf"\b{word}\b", t.upper())),
        None,
    )
    masked = next((m.group() for t in lines if (m := _MASKED.search(t))), None)
    fields = IdentityFields(
        name=_name(lines, dob_index), date_of_birth=dob, gender=gender, aadhaar_masked=masked
    )
    return ParseResult(fields, completeness(fields.name, fields.date_of_birth, masked))
