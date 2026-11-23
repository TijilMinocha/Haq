from dataclasses import dataclass
from typing import Protocol

from app.domain.models import DocumentKind
from app.schemas.document import DocumentFields


class ExtractorUnavailable(Exception):
    """The OCR engine is missing or failed; the client offers a retry."""


class UnreadableDocument(Exception):
    """The file could not be decoded or nothing useful was read; the client asks for a retake."""


@dataclass(frozen=True)
class ExtractionResult:
    fields: DocumentFields
    confidence: float


class Extractor(Protocol):
    def ready(self) -> bool:
        """Whether extraction can run right now (for the readiness check)."""
        ...

    async def extract(
        self, content: bytes, content_type: str, kind: DocumentKind
    ) -> ExtractionResult: ...
