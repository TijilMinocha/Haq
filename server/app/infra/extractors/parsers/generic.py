"""FIR, post-mortem, disability certificate and bank proof: name, date and reference."""

import re

from app.infra.extractors.ocr import OcrPage
from app.infra.extractors.parsers.common import (
    ParseResult,
    clean_name,
    completeness,
    find_value,
    parse_date,
)
from app.schemas.document import GenericFields

_NAME = re.compile(
    r"name\s*of\s*(?:the\s*)?(?:deceased|victim|injured|person|patient|applicant)|"
    r"(?<![a-z])name(?!\s*of\s*(?:father|mother|husband|informant|complainant|police))",
    re.I,
)
_REFERENCE = re.compile(
    r"(?:f\.?\s*i\.?\s*r\.?|p\.?\s*m\.?|post\s*mortem|report|certificate|ref(?:erence)?)"
    r"\s*(?:no|number)\.?",
    re.I,
)


def parse(page: OcrPage) -> ParseResult:
    reference = find_value(page, _REFERENCE)
    first_date = next((d for line in page.lines if (d := parse_date(line.text))), None)
    fields = GenericFields(
        name=clean_name(find_value(page, _NAME)),
        date=first_date,
        reference_number=reference.split()[0] if reference else None,
    )
    return ParseResult(fields, completeness(fields.name, fields.date, fields.reference_number))
