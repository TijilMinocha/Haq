import re
from datetime import date

from app.infra.extractors.ocr import OcrPage
from app.infra.extractors.parsers.common import (
    ParseResult,
    clean_name,
    completeness,
    find_value,
    parse_date,
)
from app.schemas.document import DeathCertificateFields

# Certificates print bilingual labels ("नाम / Name :"), so each label accepts either script.
_NAME = re.compile(
    r"name\s*of\s*(?:the\s*)?deceased|मृतक\s*का\s*नाम|(?<![a-z])name(?!\s*of\s*(?:father|mother|husband|wife|informant))",
    re.I,
)
_DATE_OF_DEATH = re.compile(r"date\s*of\s*death|मृत्यु\s*की\s*(?:तिथि|तारीख)", re.I)
_DATE_OF_BIRTH = re.compile(r"date\s*of\s*birth|जन्म\s*(?:की\s*)?(?:तिथि|तारीख)", re.I)
_AGE = re.compile(r"(?<![a-z])age(?:\s*at\s*death)?|आयु", re.I)
_PLACE = re.compile(r"place\s*of\s*death|मृत्यु\s*का\s*स्थान", re.I)
_REGISTRATION = re.compile(r"registration\s*(?:no|number)\.?|पंजीकरण\s*संख्या", re.I)
_CAUSE = re.compile(r"cause\s*of\s*death", re.I)


def _first_date(page: OcrPage, label: re.Pattern[str]) -> date | None:
    value = find_value(page, label)
    return parse_date(value) if value else None


def parse(page: OcrPage) -> ParseResult:
    age_text = find_value(page, _AGE)
    age_match = re.search(r"\d{1,3}", age_text or "")
    registration = find_value(page, _REGISTRATION)
    place = find_value(page, _PLACE)
    fields = DeathCertificateFields(
        deceased_name=clean_name(find_value(page, _NAME)),
        date_of_death=_first_date(page, _DATE_OF_DEATH),
        date_of_birth=_first_date(page, _DATE_OF_BIRTH),
        age=int(age_match.group()) if age_match else None,
        place_of_death=place.split(" Registration")[0].strip() if place else None,
        cause=find_value(page, _CAUSE),
        registration_number=registration.split()[0] if registration else None,
    )
    return ParseResult(fields, completeness(fields.deceased_name, fields.date_of_death))
