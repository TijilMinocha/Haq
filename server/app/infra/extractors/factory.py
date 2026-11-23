from app.core.config import Settings
from app.infra.extractors.base import Extractor
from app.infra.extractors.mock import MockExtractor
from app.infra.extractors.tesseract import TesseractExtractor


def build_extractor(settings: Settings) -> Extractor:
    if settings.extractor == "mock":
        return MockExtractor()
    return TesseractExtractor(
        settings.ocr_languages, settings.extract_min_confidence, settings.tesseract_cmd
    )
