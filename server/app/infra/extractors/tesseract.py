import asyncio
import shutil
from functools import cached_property
from typing import Any

import pytesseract

from app.domain.models import DocumentKind
from app.infra.extractors.base import ExtractionResult, ExtractorUnavailable
from app.infra.extractors.image import Image, prepare
from app.infra.extractors.ocr import OcrLine, OcrPage, OcrWord
from app.infra.extractors.pipeline import Reading, accept, read

# Passbooks are uniform tables; certificates and cards have mixed blocks of text.
_PSM = {DocumentKind.PASSBOOK: 6}
_DEFAULT_PSM = 4


def page_from_tesseract(data: dict[str, list[Any]]) -> OcrPage:
    grouped: dict[tuple[int, int, int], list[OcrWord]] = {}
    for i, text in enumerate(data["text"]):
        confidence = float(data["conf"][i])
        if not str(text).strip() or confidence < 0:
            continue
        key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
        grouped.setdefault(key, []).append(
            OcrWord(
                str(text).strip(), confidence / 100, int(data["left"][i]), int(data["width"][i])
            )
        )
    return OcrPage(
        tuple(
            OcrLine(tuple(sorted(words, key=lambda w: w.left)))
            for _, words in sorted(grouped.items())
        )
    )


class TesseractExtractor:
    """Runs OCR passes in order, e.g. "eng,hin+eng", until one parses fully.

    English goes first: the combined Hindi model misreads the digit 1 (as the danda),
    which breaks dates and amounts. Hindi is only worth its cost when English fails.
    """

    def __init__(self, passes: str, min_confidence: float, cmd: str | None = None) -> None:
        self._wanted = [p.strip() for p in passes.split(",") if p.strip()]
        self._min_confidence = min_confidence
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd

    @cached_property
    def _passes(self) -> list[str]:
        try:
            installed = set(pytesseract.get_languages(config=""))
        except (pytesseract.TesseractNotFoundError, OSError) as exc:
            raise ExtractorUnavailable("tesseract is not installed") from exc
        usable = []
        for wanted in self._wanted:
            langs = "+".join(lang for lang in wanted.split("+") if lang in installed)
            if langs and langs not in usable:
                usable.append(langs)
        if not usable:
            raise ExtractorUnavailable(f"none of {self._wanted} installed")
        return usable

    def ready(self) -> bool:
        try:
            return bool(self._passes)
        except ExtractorUnavailable:
            return False

    def _ocr(self, image: Image, kind: DocumentKind, languages: str) -> OcrPage:
        try:
            data = pytesseract.image_to_data(
                image,
                lang=languages,
                config=f"--oem 1 --psm {_PSM.get(kind, _DEFAULT_PSM)}",
                output_type=pytesseract.Output.DICT,
            )
        except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError, OSError) as exc:
            raise ExtractorUnavailable("tesseract failed") from exc
        return page_from_tesseract(data)

    def _run(self, content: bytes, content_type: str, kind: DocumentKind) -> ExtractionResult:
        image = prepare(content, content_type)
        best: Reading | None = None
        for languages in self._passes:
            reading = read(self._ocr(image, kind, languages), kind)
            if best is None or (reading.parsed.completeness, reading.confidence) > (
                best.parsed.completeness,
                best.confidence,
            ):
                best = reading
            if best.parsed.completeness == 1.0:
                break
        assert best is not None  # _passes is never empty
        return accept(best, self._min_confidence)

    async def extract(
        self, content: bytes, content_type: str, kind: DocumentKind
    ) -> ExtractionResult:
        # OCR is CPU-bound and slow; keep it off the event loop.
        return await asyncio.to_thread(self._run, content, content_type, kind)


def tesseract_available() -> bool:
    return shutil.which(pytesseract.pytesseract.tesseract_cmd) is not None
