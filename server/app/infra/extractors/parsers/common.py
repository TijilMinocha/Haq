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

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# An amount cell as a bank prints it: Indian digit grouping, paise optional, and the Dr/Cr
# marker either glued to the digits or read as a word of its own beside them. OCR also glues
# stray punctuation to a cell, which is not part of the number.
_CELL_EDGE = r"[|:;,()\[\].-]*"
_AMOUNT_CELL = re.compile(
    rf"^{_CELL_EDGE}(?P<pre>dr|cr)?{_CELL_EDGE}"
    rf"(?P<number>\d{{1,3}}(?:,\d{{2,3}})+(?:\.\d{{1,2}})?|\d+(?:\.\d{{1,2}})?)"
    rf"{_CELL_EDGE}(?P<post>dr|cr)?{_CELL_EDGE}$",
    re.I,
)
_MARKER = re.compile(r"^(dr|cr)\.?$", re.I)
# A reference number runs longer than any balance a PMJDY passbook carries.
_MAX_BARE_AMOUNT_DIGITS = 7

_SEPARATOR = re.compile(r"^\s*[:=.\-/|]+\s*")
# Words that are part of a label rather than of the value printed after it. Bilingual forms
# such as "नाम / Name :" leave the other language's label between ours and the value.
_LABEL_WORDS = frozenset(
    {
        "a/c",
        "ac",
        "account",
        "branch",
        "customer",
        "deceased",
        "father",
        "holder",
        "ifsc",
        "micr",
        "mother",
        "name",
        "no",
        "no.",
        "nominee",
        "num",
        "number",
        "of",
        "the",
        "wife",
        "का",
        "की",
        "खाता",
        "नाम",
        "नामांकित",
        "मृतक",
        "व्यक्ति",
        "शाखा",
        "संख्या",
    }
)


def normalize_digits(text: str) -> str:
    """Maps the Devanagari digits a bilingual passbook prints onto ASCII ones."""
    return text.translate(_DEVANAGARI_DIGITS)


def _year(raw: str) -> int:
    year = int(raw)
    return year + 2000 if year < 100 else year


def parse_date(text: str) -> date | None:
    """First day/month/year date in the text. Indian documents put the day first."""
    for match in DATE_PATTERN.finditer(normalize_digits(text)):
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
    return round(float(normalize_digits(text).replace(",", "")))


def cash_marker(text: str) -> str | None:
    """'dr' or 'cr' for a word that is only the marker banks print beside an amount."""
    match = _MARKER.match(text)
    return match.group(1).lower() if match else None


def parse_amount_cell(text: str) -> tuple[int, str | None] | None:
    """An amount as printed inside one table cell, with the Dr/Cr marker it arrived with.

    Bare integers are accepted because OCR drops the paise column, but only up to seven
    digits: anything longer is a reference number that happens to sit on a transaction row.
    """
    match = _AMOUNT_CELL.match(normalize_digits(text))
    if not match:
        return None
    number = match.group("number")
    if "." not in number and "," not in number and len(number) > _MAX_BARE_AMOUNT_DIGITS:
        return None
    marker = match.group("pre") or match.group("post")
    return parse_amount(number), marker.lower() if marker else None


def _strip_label_words(value: str) -> str:
    """Drops the label fragments OCR leaves between the label we matched and its value."""
    words = value.split()
    while words:
        head = words[0].strip("|/=.,-:")
        if head and not words[0].endswith(":") and head.lower() not in _LABEL_WORDS:
            break
        words.pop(0)
    return " ".join(words)


def value_after(text: str, label: re.Pattern[str]) -> str | None:
    """The text that follows a label such as 'Name :' on the same line."""
    match = label.search(text)
    if not match:
        return None
    value = _strip_label_words(_SEPARATOR.sub("", text[match.end() :]))
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
# S and B are only digits next to one; as letters they are what account codes are made of.
_AMBIGUOUS_LOOKALIKES = {"S": "5", "B": "8"}
_DATE_SHAPE = re.compile(r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$")
_AMOUNT_SHAPE = re.compile(r"^\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?$|^\d+\.\d{1,2}$")
_BARE_NUMBER = re.compile(r"^\d{2,7}$")


def _looks_numeric(text: str) -> bool:
    """True for a word that reads as a date or an amount rather than as a code."""
    if _DATE_SHAPE.match(text):
        return True
    if "." in text or "," in text:
        return bool(_AMOUNT_SHAPE.match(text))
    return bool(_BARE_NUMBER.match(text))


def fix_numeric_word(text: str) -> str:
    """Undoes OCR letter-for-digit swaps (O/0, l/1, S/5, B/8, ~/-) that hide a number.

    A swap is only trusted when it turns a word that reads as nothing into one that reads as
    a date or an amount, so IFSC codes like SBIN0001234 and narrations like UPI/P2M survive.
    """
    text = normalize_digits(text)
    fixed = text.translate(_DIGIT_LOOKALIKES)
    letters = [i for i, c in enumerate(fixed) if c.isalpha()]
    if len(letters) == 1:
        at = letters[0]
        digit = _AMBIGUOUS_LOOKALIKES.get(fixed[at])
        neighbours = fixed[max(at - 1, 0) : at] + fixed[at + 1 : at + 2]
        if digit is not None and any(c.isdigit() for c in neighbours):
            fixed = fixed[:at] + digit + fixed[at + 1 :]
    return fixed if not _looks_numeric(text) and _looks_numeric(fixed) else text


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
