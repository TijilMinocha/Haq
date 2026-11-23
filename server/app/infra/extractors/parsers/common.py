import re
from dataclasses import dataclass
from datetime import date

from app.infra.extractors.ocr import OcrLine, OcrPage, OcrWord
from app.schemas.document import DocumentFields

_MONTHS = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1
    )
}
_NUMERIC_DATE = re.compile(r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})(?!\d)")
_TEXT_DATE = re.compile(r"(?<!\d)(\d{1,2})[\s\-]([A-Za-z]{3})[A-Za-z]*[\s\-,]+(\d{4}|\d{2})(?!\d)")
DATE_PATTERN = re.compile(f"{_NUMERIC_DATE.pattern}|{_TEXT_DATE.pattern}")
# Amounts on passbooks always carry paise, which separates them from cheque and ref numbers.
AMOUNT_PATTERN = re.compile(
    r"(?<![\d.])\d{1,3}(?:,\d{2,3})*\.\d{2}(?![\d])|(?<![\d.,])\d+\.\d{2}(?!\d)"
)
_SEPARATOR = re.compile(r"^\s*[:=.\-]+\s*")


def _year(raw: str) -> int:
    year = int(raw)
    return year + 2000 if year < 100 else year


def parse_date(text: str) -> date | None:
    """First day/month/year date in the text. Indian documents put the day first."""
    for match in DATE_PATTERN.finditer(text):
        try:
            if match.group(1):
                return date(_year(match.group(3)), int(match.group(2)), int(match.group(1)))
            month = _MONTHS.get(match.group(5).lower())
            if month:
                return date(_year(match.group(6)), month, int(match.group(4)))
        except ValueError:
            continue
    return None


def parse_amount(text: str) -> int:
    return round(float(text.replace(",", "")))


def value_after(text: str, label: re.Pattern[str]) -> str | None:
    """The text that follows a label such as 'Name :' on the same line."""
    match = label.search(text)
    if not match:
        return None
    value = _SEPARATOR.sub("", text[match.end() :]).strip()
    return value or None


def find_value(page: OcrPage, label: re.Pattern[str]) -> str | None:
    for line in page.lines:
        value = value_after(line.text, label)
        if value:
            return value
    return None


def clean_name(value: str | None) -> str | None:
    """Keeps the leading run of name words and drops what OCR glued on after it."""
    if not value:
        return None
    words = []
    for word in value.split():
        if not re.fullmatch(r"[A-Za-z.ऀ-ॿ]+", word) or word.endswith(":"):
            break
        words.append(word)
    name = " ".join(words).strip(" .")
    return name.title() if name and not re.search(r"[ऀ-ॿ]", name) else name or None


@dataclass(frozen=True)
class ParseResult:
    fields: DocumentFields
    completeness: float
    """Share of the key fields found, from 0 to 1. Zero means nothing useful was read."""


def completeness(*found: object) -> float:
    return sum(1 for f in found if f) / len(found)


_DIGIT_LOOKALIKES = str.maketrans(
    {"O": "0", "o": "0", "D": "0", "l": "1", "I": "1", "|": "1", "i": "1", "~": "-", "_": "-"}
)
_NUMERIC_SHARE = 0.6


def fix_numeric_word(text: str) -> str:
    """Undoes OCR letter-for-digit swaps (O/0, l/1, ~/-) in words that are mostly digits.

    Only for table cells: applied to a header it would turn IFSC codes like SBIN into SB1N.
    """
    alnum = [c for c in text if c.isalnum()]
    if not alnum or sum(c.isdigit() for c in alnum) / len(alnum) < _NUMERIC_SHARE:
        return text
    return text.translate(_DIGIT_LOOKALIKES)


def fix_numeric_page(page: OcrPage) -> OcrPage:
    return OcrPage(
        tuple(
            OcrLine(
                tuple(
                    OcrWord(fix_numeric_word(w.text), w.confidence, w.left, w.width)
                    for w in line.words
                )
            )
            for line in page.lines
        )
    )
