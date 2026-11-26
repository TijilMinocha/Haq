"""Turns a phone photo or PDF into a clean, upright, black-on-white image for OCR."""

import cv2
import numpy as np
import pymupdf

from app.infra.extractors.base import UnreadableDocument
from app.infra.extractors.sniffing import MAX_IMAGE_PIXELS

Image = np.ndarray

_TARGET_WIDTH = 2000
_PDF_DPI = 200
_SKEW_SEARCH_DEG = 10.0
_SKEW_STEP_DEG = 0.5
_SKEW_PROBE_WIDTH = 800


def decode(content: bytes, content_type: str) -> Image:
    if content_type == "application/pdf":
        return _decode_pdf(content)
    try:
        image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    except cv2.error as exc:
        # cv2 raises rather than returning None when a header describes an absurd image.
        raise UnreadableDocument("image could not be decoded") from exc
    if image is None:
        raise UnreadableDocument("image could not be decoded")
    return image


def _decode_pdf(content: bytes) -> Image:
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            page = doc[0]
            # A few hundred bytes of PDF can describe a page kilometres wide, and rendering
            # it would allocate more memory than the instance has.
            if _pdf_pixels(page.rect) > MAX_IMAGE_PIXELS:
                raise UnreadableDocument("pdf page too large")
            pix = page.get_pixmap(dpi=_PDF_DPI, colorspace=pymupdf.csGRAY)
            return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w).copy()
    except UnreadableDocument:
        raise
    except Exception as exc:
        raise UnreadableDocument("pdf could not be rendered") from exc


def _pdf_pixels(rect: pymupdf.Rect) -> float:
    scale = _PDF_DPI / 72
    return float(rect.width) * scale * float(rect.height) * scale


def resize(gray: Image) -> Image:
    scale = _TARGET_WIDTH / gray.shape[1]
    interpolation = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    return cv2.resize(gray, None, fx=scale, fy=scale, interpolation=interpolation)


def rotate(gray: Image, angle_deg: float) -> Image:
    h, w = gray.shape
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle_deg, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def estimate_skew(gray: Image) -> float:
    """Finds the rotation that makes text rows sharpest (highest row-sum variance).

    A projection search is slower than minAreaRect but does not break on photos with
    dark borders or table lines, which phone pictures of passbooks always have.
    """
    scale = _SKEW_PROBE_WIDTH / gray.shape[1]
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    _, ink = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    best_angle, best_score = 0.0, -1.0
    for angle in np.arange(-_SKEW_SEARCH_DEG, _SKEW_SEARCH_DEG + 1e-9, _SKEW_STEP_DEG):
        rows = rotate(ink, float(angle)).sum(axis=1, dtype=np.float64)
        score = float(np.var(rows))
        if score > best_score:
            best_angle, best_score = float(angle), score
    return best_angle


def binarise(gray: Image) -> Image:
    # Adaptive thresholding copes with the uneven light and shadows of handheld photos.
    blurred = cv2.medianBlur(gray, 3)
    return cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )


def prepare(content: bytes, content_type: str) -> Image:
    gray = resize(decode(content, content_type))
    return binarise(rotate(gray, estimate_skew(gray)))
