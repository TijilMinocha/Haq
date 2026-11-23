import pymupdf

from app.core.errors import AppError
from app.domain.models import ELIGIBLE_LIKE, Scheme
from app.schemas.case import CaseView


def _ensure_applicable(view: CaseView, scheme: Scheme) -> None:
    cover = next((c for c in view.evaluation.covers if c.scheme == scheme), None)
    if cover is None or cover.status not in ELIGIBLE_LIKE:
        raise AppError(
            "form_not_applicable",
            409,
            "This case is not eligible for that scheme.",
            {"scheme": scheme},
        )


def _render(title: str, lines: list[str]) -> bytes:
    """Placeholder PDF; phase 5 overlays the official bank forms instead."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((56, 72), title, fontsize=16)
    y = 108.0
    for line in lines:
        page.insert_text((56, y), line, fontsize=11)
        y += 18
    data: bytes = doc.tobytes()
    doc.close()
    return data


def _case_lines(view: CaseView) -> list[str]:
    return [
        f"Case: {view.code}",
        f"Insured: {view.subject.name or '-'}",
        f"Event: {view.event.type or '-'} on {view.event.date or '-'}",
        f"Nominee: {view.nominee.name or '-'} ({view.nominee.relation or '-'})",
    ]


def claim_form(view: CaseView, scheme: Scheme) -> bytes:
    _ensure_applicable(view, scheme)
    return _render(f"{scheme} claim form (draft)", _case_lines(view))


def escalation_letter(view: CaseView, scheme: Scheme) -> bytes:
    _ensure_applicable(view, scheme)
    return _render(
        f"{scheme} claim escalation letter (draft)",
        [*_case_lines(view), "", "The claim above has not been settled. Please act on it."],
    )
