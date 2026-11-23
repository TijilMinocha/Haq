"""Guards the bundled official forms: a replaced PDF or a typo in a map fails here."""

import pymupdf
import pytest

from app.domain.models import Scheme
from app.infra.pdf import overlay
from app.schemas.case import CaseView
from app.services import form_service
from app.services.forms.data import build
from app.services.forms.official_values import official_values

SCHEMES = list(Scheme)


def _form(scheme: Scheme) -> overlay.OfficialForm:
    form = overlay.load_official(scheme.value)
    assert form is not None, f"{scheme.value}.pdf or .yaml missing in official/"
    return form


@pytest.mark.parametrize("scheme", SCHEMES)
def test_every_anchor_is_on_its_page(scheme: Scheme) -> None:
    form = _form(scheme)
    with pymupdf.open(form.template) as doc:
        for spot in form.spots:
            assert overlay.locate(doc[spot.page], spot) is not None, spot.anchor


@pytest.mark.parametrize("scheme", SCHEMES)
def test_every_mapped_value_exists(scheme: Scheme, sunita: CaseView) -> None:
    cover = next(c for c in sunita.evaluation.covers if c.scheme == scheme)
    known = official_values(build(sunita, cover)).keys()
    assert {spot.value for spot in _form(scheme).spots} <= known


def _value_right_of(page: pymupdf.Page, label: str) -> str:
    rect = page.search_for(label)[-1]
    clip = pymupdf.Rect(rect.x1, rect.y0 - 2, page.rect.width, rect.y1 + 2)
    return str(page.get_text(clip=clip))


def test_pmjjby_values_sit_beside_their_labels(sunita: CaseView) -> None:
    pdf = form_service.claim_form(sunita, Scheme.PMJJBY)
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        page = doc[0]
        assert "Ramesh Kumar" in _value_right_of(page, "(1) Name:")
        assert "15-11-2026" in _value_right_of(page, "(4) Date of death:")
        assert "Sunita Devi" in _value_right_of(page, "Name of the nominee:")
        assert "Wife" in _value_right_of(page, "Relationship of the nominee/claimant")
        # The official form comes first, then Haq's own pages.
        with pymupdf.open(_form(Scheme.PMJJBY).template) as blank:
            assert "Claim details" in doc[blank.page_count].get_text()


def test_rupay_values_go_in_the_table_column(sunita: CaseView) -> None:
    pdf = form_service.claim_form(sunita, Scheme.RUPAY_PMJDY)
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        page = doc[0]
        assert "Ramesh Kumar" in _value_right_of(page, "NAME OF RUPAY CARDHOLDER")
        assert "6073 92XX XXXX" in _value_right_of(page, "RUPAY CARD NUMBER")
        assert "Sunita Devi" in _value_right_of(page, "NAME OF NOMINEE")
