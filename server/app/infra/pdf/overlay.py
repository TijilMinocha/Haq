"""Writes case values onto an official, flat claim form.

Official forms are flat PDFs without fillable fields. Each scheme has a map
(official/<SCHEME>.yaml) listing where each value goes. A spot is usually anchored to the
printed label next to it ("(4) Date of death:"), so a bank's slightly shifted copy of the
same form still lines up. Fixed coordinates are a fallback for labels the PDF lacks as text;
read them off a grid with `uv run python -m scripts.calibrate_form <SCHEME>`.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf
import yaml

OFFICIAL_DIR = Path(__file__).parent / "official"
_FONT_SIZE = 9.0
_GAP_AFTER_LABEL = 6.0
_RIGHT_MARGIN = 36.0
_SAME_LINE_PT = 3.0

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class FieldSpot:
    value: str
    page: int
    anchor: str | None = None
    nth: int = 0
    """Which match of the anchor to use when the label appears more than once on the page."""
    x: float | None = None
    """Absolute left edge. With an anchor, overrides 'just after the label' (table columns)."""
    y: float | None = None
    """Absolute text top; only used without an anchor."""
    dy: float = 0.0
    size: float = _FONT_SIZE


@dataclass(frozen=True)
class OfficialForm:
    template: Path
    spots: tuple[FieldSpot, ...]


def _spot(raw: dict[str, Any]) -> FieldSpot:
    return FieldSpot(
        value=str(raw["value"]),
        page=int(raw.get("page", 0)),
        anchor=raw.get("anchor"),
        nth=int(raw.get("nth", 0)),
        x=float(raw["x"]) if "x" in raw else None,
        y=float(raw["y"]) if "y" in raw else None,
        dy=float(raw.get("dy", 0.0)),
        size=float(raw.get("size", _FONT_SIZE)),
    )


def load_official(scheme: str, directory: Path = OFFICIAL_DIR) -> OfficialForm | None:
    """The mapped official form for a scheme, if both its PDF and map are present."""
    map_path = directory / f"{scheme}.yaml"
    if not map_path.exists():
        return None
    spec = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    template = directory / spec["template"]
    if not template.exists():
        return None
    return OfficialForm(template, tuple(_spot(s) for s in spec.get("fields") or []))


def _label_rect(page: pymupdf.Page, anchor: str, nth: int) -> pymupdf.Rect | None:
    """The full extent of the nth match of a label on its line.

    One match can come back as several rects when the PDF splits the label into separate
    text runs (a list number, then the words), so all rects on that line are merged.
    """
    rects = page.search_for(anchor)
    lines: list[pymupdf.Rect] = []
    for rect in rects:
        index = next(
            (i for i, line in enumerate(lines) if abs(line.y1 - rect.y1) < _SAME_LINE_PT), None
        )
        if index is None:
            lines.append(pymupdf.Rect(rect))
        else:
            lines[index] = lines[index] | rect
    return lines[nth] if len(lines) > nth else None


def locate(page: pymupdf.Page, spot: FieldSpot) -> pymupdf.Rect | None:
    """The box a value is written into, or None when its anchor is not on the page."""
    if spot.anchor:
        label = _label_rect(page, spot.anchor, spot.nth)
        if label is None:
            return None
        left = spot.x if spot.x is not None else label.x1 + _GAP_AFTER_LABEL
        top = label.y0 + spot.dy
    elif spot.x is not None and spot.y is not None:
        left, top = spot.x, spot.y + spot.dy
    else:
        return None
    return pymupdf.Rect(left, top, page.rect.width - _RIGHT_MARGIN, top + spot.size * 3)


def fill(form: OfficialForm, values: dict[str, str | None]) -> bytes:
    doc = pymupdf.open(form.template)
    try:
        for spot in form.spots:
            value = values.get(spot.value)
            if not value or spot.page >= doc.page_count:
                continue
            page = doc[spot.page]
            box = locate(page, spot)
            if box is None:
                log.warning("anchor %r not found on page %s", spot.anchor, spot.page)
                continue
            # insert_htmlbox shapes Devanagari; plain insert_text would scramble Hindi names.
            page.insert_htmlbox(
                box,
                f'<span style="font-size:{spot.size}pt; color:#0b3d91">{_escape(value)}</span>',
            )
        data: bytes = doc.tobytes(garbage=3, deflate=True)
    finally:
        doc.close()
    return data


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
