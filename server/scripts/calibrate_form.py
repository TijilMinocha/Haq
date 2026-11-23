"""Draws a coordinate grid over an official form so its field map can be written.

Usage (from server/): uv run python -m scripts.calibrate_form PMJJBY
Writes app/infra/pdf/official/<SCHEME>-page<N>-grid.png for each page.
"""

import sys

import pymupdf

from app.infra.pdf.overlay import OFFICIAL_DIR

_STEP = 20
_LABEL_EVERY = 100


def main(scheme: str) -> None:
    template = OFFICIAL_DIR / f"{scheme.lower()}.pdf"
    doc = pymupdf.open(template)
    for number, page in enumerate(doc):
        width, height = page.rect.width, page.rect.height
        for x in range(0, int(width), _STEP):
            strong = x % _LABEL_EVERY == 0
            page.draw_line(
                (x, 0), (x, height), color=(1, 0, 0) if strong else (1, 0.8, 0.8), width=0.3
            )
            if strong:
                page.insert_text((x + 1, 8), str(x), fontsize=6, color=(1, 0, 0))
        for y in range(0, int(height), _STEP):
            strong = y % _LABEL_EVERY == 0
            page.draw_line(
                (0, y), (width, y), color=(0, 0, 1) if strong else (0.8, 0.8, 1), width=0.3
            )
            if strong:
                page.insert_text((1, y - 1), str(y), fontsize=6, color=(0, 0, 1))
        out = OFFICIAL_DIR / f"{scheme}-page{number}-grid.png"
        page.get_pixmap(dpi=110).save(out)
        print(f"wrote {out}")
    doc.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "PMJJBY")
