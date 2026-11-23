import pytest

from app.domain.models import FlagSeverity, Language, Scheme
from app.schemas.case import CaseView, Nominee
from app.schemas.evaluation import Flag
from app.services.forms.blockers import describe
from app.services.forms.data import build, format_inr

from .conftest import scenario_view


@pytest.mark.parametrize(
    ("rupees", "text"),
    [(0, "₹0"), (436, "₹436"), (4564, "₹4,564"), (100000, "₹1,00,000"), (12345678, "₹1,23,45,678")],
)
def test_format_inr(rupees: int, text: str) -> None:
    assert format_inr(rupees) == text


def _cover(view: CaseView, scheme: Scheme):  # type: ignore[no-untyped-def]
    return next(c for c in view.evaluation.covers if c.scheme == scheme)


def test_sunita_pmsby_form_data(sunita: CaseView) -> None:
    f = build(sunita, _cover(sunita, Scheme.PMSBY))
    assert f.claim_amount == "₹2,00,000"
    assert f.account == "XXXXXXXX4417"
    assert (f.claimant_name, f.claimant_relation.en if f.claimant_relation else None) == (
        "Sunita Devi",
        "Wife",
    )
    assert f.deadline_date == "15-12-2026"
    assert [e.narration for e in f.evidence] == ["PMSBY PREMIUM"]
    assert len(f.blockers) == 2
    assert {d.name.en.split(" (")[0] for d in f.documents if not d.received} >= {"FIR"}


def test_rupay_form_shows_last_card_use(sunita: CaseView) -> None:
    f = build(sunita, _cover(sunita, Scheme.RUPAY_PMJDY))
    assert f.card_last_use == "30-10-2026"


def test_missing_nominee_is_called_out() -> None:
    view = scenario_view("sunita_accident", nominee=Nominee())
    view = view.model_copy(
        update={
            "documents": [
                d.model_copy(update={"fields": d.fields.model_copy(update={"nominee_name": None})})
                if d.kind.value == "passbook"
                else d
                for d in view.documents
            ]
        }
    )
    f = build(view, _cover(view, Scheme.PMJJBY))
    assert f.nominee_missing and f.claimant_name is None


@pytest.mark.parametrize(
    ("flag", "en_part", "hi_part"),
    [
        (
            Flag(
                code="name_mismatch",
                severity=FlagSeverity.BLOCKER,
                params={"documents": ["passbook", "death_certificate"], "values": ["A B", "A C"]},
                message="",
            ),
            '"A C" on the death certificate',
            "मृत्यु प्रमाण पत्र",
        ),
        (
            Flag(
                code="accident_docs_missing",
                severity=FlagSeverity.BLOCKER,
                params={"missing": ["fir", "postmortem"]},
                message="",
            ),
            "FIR (police report), Post-mortem report",
            "पोस्टमार्टम",
        ),
        (
            Flag(code="nominee_missing", severity=FlagSeverity.BLOCKER, message=""),
            "legal-heir",
            "वारिस",
        ),
        (
            Flag(
                code="account_mismatch",
                severity=FlagSeverity.BLOCKER,
                params={"accounts": ["1111", "2222"]},
                message="",
            ),
            "XXXX1111, XXXX2222",
            "प्रीमियम",
        ),
        (
            Flag(code="something_new", severity=FlagSeverity.BLOCKER, message="fallback"),
            "fallback",
            "fallback",
        ),
    ],
)
def test_blocker_text(flag: Flag, en_part: str, hi_part: str) -> None:
    en, hi = describe(flag)
    assert en_part in en and hi_part in hi


def test_language_does_not_change_data(sunita: CaseView) -> None:
    english = sunita.model_copy(update={"language": Language.EN})
    assert build(english, _cover(english, Scheme.PMJJBY)) == build(
        sunita, _cover(sunita, Scheme.PMJJBY)
    )
