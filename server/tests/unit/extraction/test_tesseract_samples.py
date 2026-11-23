"""End-to-end OCR on the synthetic sample photos. Needs the tesseract binary; skipped without it.
Run in Docker: docker build --target test -t haq-test server && docker run --rm haq-test
"""

import pytest

from app.domain.models import DocumentKind
from app.infra.extractors.tesseract import TesseractExtractor, tesseract_available
from app.schemas.document import fields_model

from .helpers import SAMPLE_NAMES, expected, sample_bytes

pytestmark = [
    pytest.mark.tesseract,
    pytest.mark.skipif(not tesseract_available(), reason="tesseract not installed"),
]


@pytest.mark.parametrize("name", SAMPLE_NAMES)
async def test_sample_extracts_exactly(name: str) -> None:
    spec = expected(name)
    kind = DocumentKind(spec["kind"])
    result = await TesseractExtractor("eng,hin+eng", 0.35).extract(
        sample_bytes(name), "image/png", kind
    )
    assert result.fields == fields_model(kind).model_validate(spec["fields"])
    assert result.confidence >= 0.6
