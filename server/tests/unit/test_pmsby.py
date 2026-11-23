import pytest

from app.domain.facts import CaseFacts
from app.domain.models import CoverStatus, EventType
from app.domain.rules import pmsby

from .factories import CONFIG, claim, protect
from .factories import pmsby as premium


@pytest.mark.parametrize(
    ("facts", "status", "amount", "reason"),
    [
        pytest.param(claim(), CoverStatus.NOT_FOUND, 0, "no_premium_found", id="no-premium"),
        pytest.param(
            claim(premium(), event=EventType.NATURAL_DEATH),
            CoverStatus.INELIGIBLE,
            0,
            "accident_only_cover",
            id="natural-death",
        ),
        pytest.param(
            claim(premium("2025-05-30")),
            CoverStatus.LAPSED,
            0,
            "no_premium_this_cover_year",
            id="lapsed",
        ),
        pytest.param(
            claim(premium()),
            CoverStatus.ELIGIBLE,
            200000,
            "premium_debited_current_year",
            id="accident",
        ),
        pytest.param(
            claim(premium(), event=EventType.ACCIDENTAL_DISABILITY),
            CoverStatus.NEEDS_VERIFICATION,
            200000,
            "premium_debited_current_year",
            id="disability",
        ),
    ],
)
def test_cover_status(facts: CaseFacts, status: CoverStatus, amount: int, reason: str) -> None:
    cover = pmsby.evaluate(facts, CONFIG).cover
    assert (cover.status, cover.amount) == (status, amount)
    assert cover.reasons[0].code == reason


def test_disability_asks_for_extent() -> None:
    cover = pmsby.evaluate(claim(premium(), event=EventType.ACCIDENTAL_DISABILITY), CONFIG).cover
    assert cover.reasons[1].code == "disability_extent_needed"
    assert cover.reasons[1].params == {"total": 200000, "partial": 100000}


def test_protect_active_alert() -> None:
    assert [a.code for a in pmsby.evaluate(protect(premium()), CONFIG).alerts] == [
        "alert.cover_active"
    ]
