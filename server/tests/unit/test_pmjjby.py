from dataclasses import replace

import pytest

from app.domain.facts import CaseFacts
from app.domain.models import CoverStatus, EventType
from app.domain.rules import pmjjby

from .factories import CONFIG, claim, d, protect
from .factories import pmjjby as premium


@pytest.mark.parametrize(
    ("facts", "status", "amount", "reason"),
    [
        pytest.param(claim(), CoverStatus.NOT_FOUND, 0, "no_premium_found", id="no-premium"),
        pytest.param(
            claim(premium("2025-05-29")),
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
            id="accident-eligible",
        ),
        pytest.param(
            claim(premium(), event=EventType.NATURAL_DEATH),
            CoverStatus.ELIGIBLE,
            200000,
            "premium_debited_current_year",
            id="natural-eligible",
        ),
        pytest.param(
            claim(premium(), event=EventType.ACCIDENTAL_DISABILITY),
            CoverStatus.INELIGIBLE,
            0,
            "life_cover_death_only",
            id="disability",
        ),
        pytest.param(
            replace(claim(premium()), subject_dob=d("1970-01-01")),
            CoverStatus.INELIGIBLE,
            0,
            "age_above_limit",
            id="over-age",
        ),
        pytest.param(
            claim(premium("2026-11-20")),
            CoverStatus.LAPSED,
            0,
            "no_premium_this_cover_year",
            id="debit-after-event",
        ),
    ],
)
def test_cover_status(facts: CaseFacts, status: CoverStatus, amount: int, reason: str) -> None:
    cover = pmjjby.evaluate(facts, CONFIG).cover
    assert (cover.status, cover.amount) == (status, amount)
    assert cover.reasons[0].code == reason


def test_natural_death_within_lien_period_is_not_payable() -> None:
    facts = replace(
        claim(premium("2026-06-20"), event=EventType.NATURAL_DEATH), event_date=d("2026-07-10")
    )
    result = pmjjby.evaluate(facts, CONFIG)
    assert result.cover.status is CoverStatus.INELIGIBLE
    assert result.cover.reasons[0].params == {"days_since_enrolment": 20, "lien_days": 30}
    assert [f.code for f in result.flags] == ["death_within_lien_period"]


def test_accident_within_lien_period_is_payable() -> None:
    facts = replace(claim(premium("2026-06-20")), event_date=d("2026-07-10"))
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_renewal_is_not_a_new_enrolment() -> None:
    facts = replace(
        claim(premium("2025-05-28"), premium("2026-05-28"), event=EventType.NATURAL_DEATH),
        event_date=d("2026-06-10"),
    )
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_unknown_event_is_likely_eligible_without_deadline() -> None:
    result = pmjjby.evaluate(claim(premium(), event=None), CONFIG)
    assert result.cover.status is CoverStatus.LIKELY_ELIGIBLE
    assert result.deadlines == ()


def test_claim_deadline_is_soft_30_days() -> None:
    (deadline,) = pmjjby.evaluate(claim(premium()), CONFIG).deadlines
    assert (deadline.due_date, deadline.days_left, deadline.hard) == (d("2026-12-15"), 22, False)


def test_protect_active_and_lapsed_alerts() -> None:
    assert [a.code for a in pmjjby.evaluate(protect(premium()), CONFIG).alerts] == [
        "alert.cover_active"
    ]
    lapsed = pmjjby.evaluate(protect(premium("2025-05-29")), CONFIG)
    assert lapsed.cover.status is CoverStatus.LAPSED
    assert [(a.code, a.params) for a in lapsed.alerts] == [
        ("alert.cover_lapsed", {"last_debit": "2025-05-29"})
    ]
