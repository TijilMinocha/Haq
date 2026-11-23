"""HTML to PDF with PyMuPDF's Story engine.

Story shapes complex scripts and ships a Noto Devanagari fallback font, so Hindi renders
correctly with no font files of our own.
"""

import io
from pathlib import Path
from typing import Any

import jinja2
import pymupdf

_LAYOUTS = Path(__file__).parent / "layouts"
_PAGE = pymupdf.paper_rect("a4")
_MARGIN = 40

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_LAYOUTS),
    autoescape=jinja2.select_autoescape(["html", "j2"]),
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_html(layout: str, **context: Any) -> str:
    return _env.get_template(layout).render(**context)


def html_to_pdf(html: str, css: str = "") -> bytes:
    story = pymupdf.Story(html, user_css=css)
    buffer = io.BytesIO()
    writer = pymupdf.DocumentWriter(buffer)
    content = pymupdf.Rect(_MARGIN, _MARGIN, _PAGE.width - _MARGIN, _PAGE.height - _MARGIN)
    more = True
    while more:
        device = writer.begin_page(_PAGE)
        more, _ = story.place(content)
        story.draw(device)
        writer.end_page()
    writer.close()
    return buffer.getvalue()


def stylesheet() -> str:
    return (_LAYOUTS / "base.css").read_text(encoding="utf-8")


def render_pdf(layout: str, **context: Any) -> bytes:
    return html_to_pdf(render_html(layout, **context), stylesheet())


def join_pdfs(parts: list[bytes]) -> bytes:
    combined = pymupdf.open()
    for part in parts:
        with pymupdf.open(stream=part, filetype="pdf") as doc:
            combined.insert_pdf(doc)
    data: bytes = combined.tobytes(garbage=3, deflate=True)
    combined.close()
    return data
