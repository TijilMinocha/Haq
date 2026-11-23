from dataclasses import dataclass

from app.domain.models import DocumentKind
from app.infra.extractors.base import ExtractionResult, UnreadableDocument
from app.infra.extractors.masking import mask_text
from app.infra.extractors.ocr import OcrLine, OcrPage, OcrWord
from app.infra.extractors.parsers import parser_for
from app.infra.extractors.parsers.common import ParseResult


def mask_page(page: OcrPage) -> OcrPage:
    return OcrPage(
        tuple(
            OcrLine(
                tuple(OcrWord(mask_text(w.text), w.confidence, w.left, w.width) for w in line.words)
            )
            for line in page.lines
        )
    )


def _mask_lines(page: OcrPage) -> OcrPage:
    # Numbers split across words ("1234 5678 9012") only match once the line is joined.
    lines = []
    for line in mask_page(page).lines:
        joined = mask_text(line.text)
        if joined == line.text:
            lines.append(line)
            continue
        first = line.words[0]
        confidence = sum(w.confidence for w in line.words) / len(line.words)
        lines.append(OcrLine((OcrWord(joined, confidence, first.left, first.width),)))
    return OcrPage(tuple(lines))


@dataclass(frozen=True)
class Reading:
    parsed: ParseResult
    confidence: float


def read(page: OcrPage, kind: DocumentKind) -> Reading:
    """Masks identifiers, parses the page for its document kind and scores the result."""
    parsed = parser_for(kind)(_mask_lines(page))
    # OCR certainty alone is not enough: a crisp photo of the wrong page parses to nothing.
    confidence = round(page.confidence * (0.5 + 0.5 * parsed.completeness), 3)
    return Reading(parsed, confidence)


def accept(reading: Reading, min_confidence: float) -> ExtractionResult:
    if reading.parsed.completeness == 0 or reading.confidence < min_confidence:
        raise UnreadableDocument(f"confidence {reading.confidence}")
    return ExtractionResult(reading.parsed.fields, reading.confidence)


def interpret(page: OcrPage, kind: DocumentKind, min_confidence: float) -> ExtractionResult:
    return accept(read(page, kind), min_confidence)
