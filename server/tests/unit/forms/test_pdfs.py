from pathlib import Path

import pymupdf
import pytest

from app.core.errors import AppError
from app.domain.models import Language, Scheme
from app.infra.pdf import overlay
from app.schemas.case import CaseView
from app.services import form_service

from .conftest import scenario_view


def _pages(data: bytes) -> list[str]:
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        return [page.get_text() for page in doc]


def _has_devanagari_font(data: bytes) -> bool:
    # Text pulled back out of shaped Hindi is lossy, so check the embedded font instead.
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        return any("Devanagari" in f[3] for page in doc for f in page.get_fonts())


@pytest.mark.parametrize("scheme", [Scheme.PMJJBY, Scheme.PMSBY, Scheme.RUPAY_PMJDY])
def test_claim_form_carries_the_case(sunita: CaseView, scheme: Scheme) -> None:
    pdf = form_service.claim_form(sunita, scheme)
    text = " ".join(_pages(pdf))
    for expected in ("Ramesh Kumar", "Sunita Devi", "XXXXXXXX4417", "HAQ-7K3P", "₹2,00,000"):
        assert expected in text
    assert "दावा" in text
    assert _has_devanagari_font(pdf)
    assert ("FIR number" in text) is (scheme is not Scheme.PMJJBY)


def test_escalation_letter_puts_family_language_first(sunita: CaseView) -> None:
    hindi_first = _pages(form_service.escalation_letter(sunita, Scheme.PMJJBY))
    assert len(hindi_first) == 2
    assert "शाखा" in hindi_first[0] and "Branch Manager" not in hindi_first[0]
    assert "Branch Manager" in hindi_first[1]

    english = sunita.model_copy(update={"language": Language.EN})
    english_first = _pages(form_service.escalation_letter(english, Scheme.PMJJBY))
    assert "Branch Manager" in english_first[0]


def test_form_refused_for_ineligible_scheme() -> None:
    meena = scenario_view("meena_lien")
    with pytest.raises(AppError) as err:
        form_service.claim_form(meena, Scheme.PMJJBY)
    assert err.value.code == "form_not_applicable"


def _official_dir(tmp_path: Path, with_template: bool = True) -> Path:
    if with_template:
        doc = pymupdf.open()
        doc.new_page().insert_text((50, 60), "OFFICIAL PMJJBY CLAIM FORM")
        doc.save(tmp_path / "PMJJBY.pdf")
    (tmp_path / "PMJJBY.yaml").write_text(
        "template: PMJJBY.pdf\nfields:\n"
        "  insured_name: { page: 0, x: 200, y: 120, width: 250 }\n"
        "  claimant_name: { page: 0, x: 200, y: 160, width: 250 }\n",
        encoding="utf-8",
    )
    return tmp_path


def test_official_form_needs_template_and_map(tmp_path: Path) -> None:
    assert overlay.load_official("PMJJBY", tmp_path) is None
    assert overlay.load_official("PMJJBY", _official_dir(tmp_path, with_template=False)) is None


def test_official_form_values_land_in_their_spots(tmp_path: Path) -> None:
    form = overlay.load_official("PMJJBY", _official_dir(tmp_path))
    assert form is not None
    data = overlay.fill(form, {"insured_name": "रमेश कुमार", "claimant_name": "Sunita Devi"})
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        page = doc[0]
        assert "OFFICIAL PMJJBY" in page.get_text()
        assert "Sunita Devi" in page.get_text(clip=pymupdf.Rect(190, 145, 460, 185))
        assert "रमेश" in page.get_text(clip=pymupdf.Rect(190, 105, 460, 145))


def test_official_form_goes_on_top_of_haq_pages(
    sunita: CaseView, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    official_dir = _official_dir(tmp_path)
    original = overlay.load_official
    monkeypatch.setattr(overlay, "load_official", lambda scheme: original(scheme, official_dir))
    pages = _pages(form_service.claim_form(sunita, Scheme.PMJJBY))
    assert "OFFICIAL PMJJBY" in pages[0]
    assert "Claim details" in pages[1]
