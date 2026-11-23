import re
from datetime import date

from app.infra.extractors.ocr import OcrPage
from app.infra.extractors.parsers.common import ParseResult, clean_name, completeness
from app.schemas.document import CardFields

# Matches the already-masked form "6073 92XX XXXX 1234".
_MASKED_CARD = re.compile(r"(\d{4})\s?(\d{2})XX\s?XXXX\s?(\d{4})")
_VALID_FROM = re.compile(
    r"(?:valid\s*from|member\s*since|issued)\D{0,6}(\d{2})\s*/\s*(\d{2,4})", re.I
)
_CARD_WORDS = re.compile(r"rupay|valid|thru|debit|card|bank|platinum|classic", re.I)


def parse(page: OcrPage) -> ParseResult:
    text = "\n".join(line.text for line in page.lines)
    number = _MASKED_CARD.search(text)
    valid = _VALID_FROM.search(text)
    valid_from = None
    if valid:
        year = int(valid.group(2))
        valid_from = date(year + 2000 if year < 100 else year, int(valid.group(1)), 1)
    holder = next(
        (
            clean_name(line.text)
            for line in reversed(page.lines)
            if re.fullmatch(r"[A-Z][A-Z .]{3,}", line.text.strip())
            and not _CARD_WORDS.search(line.text)
        ),
        None,
    )
    fields = CardFields(
        card_bin=f"{number.group(1)}{number.group(2)}" if number else None,
        card_last4=number.group(3) if number else None,
        valid_from=valid_from,
        name=holder,
    )
    return ParseResult(fields, completeness(fields.card_bin, fields.valid_from))
