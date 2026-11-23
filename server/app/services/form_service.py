from app.core.errors import AppError
from app.domain.models import ELIGIBLE_LIKE, Language, Scheme
from app.infra.pdf import overlay
from app.infra.pdf.render import join_pdfs, render_pdf
from app.schemas.case import CaseView
from app.schemas.evaluation import CoverResult
from app.services.forms.data import FormData, build
from app.services.forms.official_values import official_values


def _applicable_cover(view: CaseView, scheme: Scheme) -> CoverResult:
    cover = next((c for c in view.evaluation.covers if c.scheme == scheme), None)
    if cover is None or cover.status not in ELIGIBLE_LIKE:
        raise AppError(
            "form_not_applicable",
            409,
            "This case is not eligible for that scheme.",
            {"scheme": scheme},
        )
    return cover


def _form_data(view: CaseView, scheme: Scheme) -> FormData:
    return build(view, _applicable_cover(view, scheme))


def claim_form(view: CaseView, scheme: Scheme) -> bytes:
    data = _form_data(view, scheme)
    details = render_pdf("claim_form.html.j2", f=data)
    official = overlay.load_official(scheme.value)
    if official is None:
        return details
    # Branches want their own form on top; Haq's pages carry the checklist and evidence.
    return join_pdfs([overlay.fill(official, official_values(data)), details])


def escalation_letter(view: CaseView, scheme: Scheme) -> bytes:
    """One letter in Hindi and English, the family's language first: the family reads one
    copy and the branch staff the other."""
    data = _form_data(view, scheme)
    order = ["hi", "en"] if view.language is Language.HI else ["en", "hi"]
    return join_pdfs([render_pdf("escalation_letter.html.j2", f=data, lang=lang) for lang in order])
