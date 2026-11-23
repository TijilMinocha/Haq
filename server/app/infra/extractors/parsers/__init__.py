from collections.abc import Callable

from app.domain.models import DocumentKind
from app.infra.extractors.ocr import OcrPage
from app.infra.extractors.parsers import aadhaar, card, death_certificate, generic, passbook
from app.infra.extractors.parsers.common import ParseResult

Parser = Callable[[OcrPage], ParseResult]

PARSERS: dict[DocumentKind, Parser] = {
    DocumentKind.PASSBOOK: passbook.parse,
    DocumentKind.DEATH_CERTIFICATE: death_certificate.parse,
    DocumentKind.AADHAAR_DECEASED: aadhaar.parse,
    DocumentKind.AADHAAR_NOMINEE: aadhaar.parse,
    DocumentKind.RUPAY_CARD: card.parse,
}


def parser_for(kind: DocumentKind) -> Parser:
    return PARSERS.get(kind, generic.parse)
