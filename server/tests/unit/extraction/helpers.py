import json
from pathlib import Path
from typing import Any

from app.infra.extractors.mock import SAMPLES_DIR
from app.infra.extractors.ocr import OcrPage


def page(text: str) -> OcrPage:
    return OcrPage.from_text("\n".join(line.strip() for line in text.strip().splitlines()))


def expected(name: str) -> dict[str, Any]:
    spec: dict[str, Any] = json.loads((SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return spec


def sample_bytes(name: str) -> bytes:
    return Path(SAMPLES_DIR / f"{name}.png").read_bytes()


SAMPLE_NAMES = sorted(p.stem for p in SAMPLES_DIR.glob("*.png"))
