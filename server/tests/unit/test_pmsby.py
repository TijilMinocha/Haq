from dataclasses import replace
from datetime import date

import pytest

from app.domain.facts import CaseFacts
from app.domain.models import CoverStatus, EventType
from app.domain.rules import pmsby

from .factories import CONFIG, EVENT, claim, d, protect, txn
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


def _dob_turning(day: date, age: int) -> date:
    """The date of birth that makes `day` the person's `age`-th birthday."""
    return date(day.year - age, day.month, day.day)


def test_covered_on_the_day_before_the_age_limit() -> None:
    dob = _dob_turning(d("2026-11-16"), CONFIG.pmsby.max_cover_age)
    facts = replace(claim(premium()), subject_dob=dob)
    assert pmsby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_not_covered_on_the_day_of_the_age_limit_birthday() -> None:
    limit = CONFIG.pmsby.max_cover_age
    facts = replace(claim(premium()), subject_dob=_dob_turning(EVENT, limit))
    cover = pmsby.evaluate(facts, CONFIG).cover
    assert cover.status is CoverStatus.INELIGIBLE
    assert cover.reasons[0].params == {"max_age": limit}


def test_29_february_birthday_reaches_the_age_limit_on_1_march() -> None:
    # Born 29 February 1956, so the 70th birthday is 1 March 2026: 2026 is not a leap year.
    facts = replace(
        claim(premium("2025-05-28")), subject_dob=date(1956, 2, 29), today=d("2026-03-10")
    )
    day_before = replace(facts, event_date=d("2026-02-28"))
    on_the_day = replace(facts, event_date=d("2026-03-01"))
    assert pmsby.evaluate(day_before, CONFIG).cover.status is CoverStatus.ELIGIBLE
    assert pmsby.evaluate(on_the_day, CONFIG).cover.status is CoverStatus.INELIGIBLE


def test_no_dob_is_not_treated_as_over_age() -> None:
    facts = claim(premium())
    assert facts.subject_dob is None
    assert pmsby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_accidental_death_pays_the_full_sum() -> None:
    cover = pmsby.evaluate(claim(premium()), CONFIG).cover
    assert (cover.status, cover.amount) == (
        CoverStatus.ELIGIBLE,
        CONFIG.pmsby.death_or_total_disability,
    )


def test_disability_asks_for_extent() -> None:
    cover = pmsby.evaluate(claim(premium(), event=EventType.ACCIDENTAL_DISABILITY), CONFIG).cover
    assert cover.reasons[1].code == "disability_extent_needed"
    assert cover.reasons[1].params == {
        "total": CONFIG.pmsby.death_or_total_disability,
        "partial": CONFIG.pmsby.partial_disability,
    }
    # Paid in full until the certificate says the disability is partial.
    assert cover.amount == CONFIG.pmsby.death_or_total_disability


def test_a_premium_of_the_wrong_amount_is_not_cover() -> None:
    facts = claim(txn("2026-05-30", "PMSBY PREMIUM", 436))
    assert pmsby.evaluate(facts, CONFIG).cover.status is CoverStatus.NOT_FOUND


def test_protect_active_alert() -> None:
    assert [a.code for a in pmsby.evaluate(protect(premium()), CONFIG).alerts] == [
        "alert.cover_active"
    ]
