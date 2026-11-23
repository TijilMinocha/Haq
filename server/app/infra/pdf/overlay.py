"""Writes case values onto an official, flat bank claim form at calibrated positions.

Official forms are scanned or flat PDFs without fillable fields, so each scheme has a map
(official/<SCHEME>.yaml) of where every value goes. Calibrate a map with
`uv run python -m scripts.calibrate_form <SCHEME>`.
"""

from dataclasses import dataclass
from pathlib import Path

import pymupdf
import yaml

OFFICIAL_DIR = Path(__file__).parent / "official"
_FONT_SIZE = 9.0


@dataclass(frozen=True)
class FieldSpot:
    key: str
    page: int
    x: float
    y: float
    width: float
    size: float


@dataclass(frozen=True)
class OfficialForm:
    template: Path
    spots: tuple[FieldSpot, ...]


def load_official(scheme: str, directory: Path = OFFICIAL_DIR) -> OfficialForm | None:
    """The calibrated official form for a scheme, if both its PDF and map are present."""
    map_path = directory / f"{scheme}.yaml"
    if not map_path.exists():
        return None
    spec = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    template = directory / spec["template"]
    if not template.exists():
        return None
    spots = tuple(
        FieldSpot(
            key=key,
            page=int(s.get("page", 0)),
            x=float(s["x"]),
            y=float(s["y"]),
            width=float(s.get("width", 200)),
            size=float(s.get("size", _FONT_SIZE)),
        )
        for key, s in (spec.get("fields") or {}).items()
    )
    return OfficialForm(template, spots)


def fill(form: OfficialForm, values: dict[str, str | None]) -> bytes:
    doc = pymupdf.open(form.template)
    try:
        for spot in form.spots:
            value = values.get(spot.key)
            if not value or spot.page >= doc.page_count:
                continue
            page = doc[spot.page]
            box = pymupdf.Rect(
                spot.x, spot.y - spot.size, spot.x + spot.width, spot.y + spot.size * 3
            )
            # insert_htmlbox shapes Devanagari; plain insert_text would scramble Hindi names.
            page.insert_htmlbox(
                box, f'<span style="font-size:{spot.size}pt">{_escape(value)}</span>'
            )
        data: bytes = doc.tobytes(garbage=3, deflate=True)
    finally:
        doc.close()
    return data


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
