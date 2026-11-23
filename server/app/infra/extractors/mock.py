"""Returns known fields for the bundled sample images, so demos and tests never depend on OCR.

Any other file gets empty fields with zero confidence; the user fills them in by hand.
"""

import hashlib
import json
from pathlib import Path

from app.domain.models import DocumentKind
from app.infra.extractors.base import ExtractionResult
from app.schemas.document import DocumentFields, fields_model

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "services" / "stubs" / "samples"
_MOCK_CONFIDENCE = 0.95


def sample_index(samples_dir: Path = SAMPLES_DIR) -> dict[str, tuple[DocumentKind, DocumentFields]]:
    """Maps the SHA-256 of each sample image to the fields it should produce."""
    index: dict[str, tuple[DocumentKind, DocumentFields]] = {}
    for expected in samples_dir.glob("*.json"):
        image = expected.with_suffix(".png")
        if not image.exists():
            continue
        spec = json.loads(expected.read_text(encoding="utf-8"))
        kind = DocumentKind(spec["kind"])
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        index[digest] = (kind, fields_model(kind).model_validate(spec["fields"]))
    return index


class MockExtractor:
    def __init__(self, samples_dir: Path = SAMPLES_DIR) -> None:
        self._index = sample_index(samples_dir)

    def ready(self) -> bool:
        return True

    async def extract(
        self, content: bytes, content_type: str, kind: DocumentKind
    ) -> ExtractionResult:
        known = self._index.get(hashlib.sha256(content).hexdigest())
        if known and known[0] is kind:
            return ExtractionResult(known[1], _MOCK_CONFIDENCE)
        return ExtractionResult(fields_model(kind)(), 0.0)
