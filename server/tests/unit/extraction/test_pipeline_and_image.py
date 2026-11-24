import cv2
import numpy as np
import pytest

from app.domain.models import DocumentKind
from app.infra.extractors.base import UnreadableDocument
from app.infra.extractors.image import decode, estimate_skew, prepare, resize
from app.infra.extractors.mock import MockExtractor
from app.infra.extractors.ocr import OcrPage
from app.infra.extractors.pipeline import interpret
from app.schemas.document import PassbookFields

from .helpers import SAMPLE_NAMES, expected, sample_bytes


def test_samples_exist() -> None:
    assert len(SAMPLE_NAMES) >= 6


def test_garbage_bytes_are_unreadable() -> None:
    with pytest.raises(UnreadableDocument):
        decode(b"not an image", "image/jpeg")


def test_skew_of_sample_photo_is_found() -> None:
    gray = resize(decode(sample_bytes("sunita_passbook"), "image/png"))
    # The samples are tilted 2 degrees counter-clockwise, so the fix is about -2.
    assert abs(estimate_skew(gray) + 2.0) <= 0.5


def test_prepare_returns_binary_image() -> None:
    image = prepare(sample_bytes("sunita_passbook"), "image/png")
    assert set(np.unique(image)) <= {0, 255}
    assert image.shape[1] == 2000


def test_pdf_first_page_is_rendered() -> None:
    import pymupdf

    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Name: RAMESH KUMAR")
    pdf = doc.tobytes()
    gray = decode(pdf, "application/pdf")
    assert gray.ndim == 2 and gray.min() < 128


def test_interpret_rejects_pages_with_nothing_useful() -> None:
    with pytest.raises(UnreadableDocument):
        interpret(OcrPage.from_text("lorem ipsum"), DocumentKind.PASSBOOK, 0.35)


def test_interpret_scales_confidence_by_completeness() -> None:
    page = OcrPage.from_text("Name: RAMESH KUMAR", confidence=0.9)
    result = interpret(page, DocumentKind.PASSBOOK, 0.1)
    assert result.confidence == pytest.approx(0.9 * (0.5 + 0.5 * 0.25), abs=1e-3)


async def test_mock_returns_sample_fields() -> None:
    result = await MockExtractor().extract(
        sample_bytes("sunita_passbook"), "image/png", DocumentKind.PASSBOOK
    )
    assert result.fields == PassbookFields.model_validate(expected("sunita_passbook")["fields"])
    assert result.confidence > 0.9


async def test_mock_is_lenient_with_unknown_or_mismatched_files() -> None:
    unknown = await MockExtractor().extract(b"x", "image/png", DocumentKind.FIR)
    assert unknown.confidence == 0
    wrong_kind = await MockExtractor().extract(
        sample_bytes("sunita_passbook"), "image/png", DocumentKind.FIR
    )
    assert wrong_kind.confidence == 0


def test_blank_white_image_has_no_skew() -> None:
    blank = np.full((400, 800), 255, dtype=np.uint8)
    ok, png = cv2.imencode(".png", blank)
    assert ok
    assert estimate_skew(resize(decode(png.tobytes(), "image/png"))) == pytest.approx(0.0, abs=10.0)
