from dataclasses import replace
from datetime import date, timedelta

import pytest

from app.domain.facts import CaseFacts
from app.domain.models import CoverStatus, EventType
from app.domain.rules import pmjjby

from .factories import CONFIG, EVENT, claim, d, protect, txn
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


def _dob_turning(day: date, age: int) -> date:
    """The date of birth that makes `day` the person's `age`-th birthday."""
    return date(day.year - age, day.month, day.day)


def test_covered_on_the_day_before_the_age_limit() -> None:
    dob = _dob_turning(d("2026-11-16"), CONFIG.pmjjby.max_cover_age)
    facts = replace(claim(premium()), subject_dob=dob)
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_not_covered_on_the_day_of_the_age_limit_birthday() -> None:
    limit = CONFIG.pmjjby.max_cover_age
    facts = replace(claim(premium()), subject_dob=_dob_turning(EVENT, limit))
    cover = pmjjby.evaluate(facts, CONFIG).cover
    assert cover.status is CoverStatus.INELIGIBLE
    assert cover.reasons[0].params == {"max_age": limit}


def test_29_february_birthday_reaches_the_age_limit_on_1_march() -> None:
    # Born 29 February 1972, so the 55th birthday is 1 March 2027: 2027 is not a leap year.
    facts = replace(
        claim(premium("2026-05-28")), subject_dob=date(1972, 2, 29), today=d("2027-03-10")
    )
    day_before = replace(facts, event_date=d("2027-02-28"))
    on_the_day = replace(facts, event_date=d("2027-03-01"))
    assert pmjjby.evaluate(day_before, CONFIG).cover.status is CoverStatus.ELIGIBLE
    assert pmjjby.evaluate(on_the_day, CONFIG).cover.status is CoverStatus.INELIGIBLE


def test_no_dob_is_not_treated_as_over_age() -> None:
    facts = claim(premium())
    assert facts.subject_dob is None
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


@pytest.mark.parametrize(
    ("debit", "event", "status"),
    [
        pytest.param("2026-05-25", "2027-05-31", CoverStatus.ELIGIBLE, id="window-start"),
        pytest.param("2026-05-31", "2027-05-31", CoverStatus.ELIGIBLE, id="window-end"),
        pytest.param("2026-06-01", "2027-05-31", CoverStatus.ELIGIBLE, id="year-start"),
        pytest.param("2026-05-25", "2027-06-01", CoverStatus.LAPSED, id="window-start-next-year"),
        pytest.param("2026-05-31", "2027-06-01", CoverStatus.LAPSED, id="window-end-next-year"),
        pytest.param("2026-06-01", "2027-06-01", CoverStatus.LAPSED, id="year-start-next-year"),
        pytest.param("2027-05-25", "2027-06-01", CoverStatus.ELIGIBLE, id="next-renewal"),
        pytest.param("2027-06-01", "2027-06-01", CoverStatus.ELIGIBLE, id="debit-on-the-day"),
    ],
)
def test_cover_year_turns_over_on_1_june(debit: str, event: str, status: CoverStatus) -> None:
    facts = replace(claim(premium(debit)), event_date=d(event), today=d(event))
    assert pmjjby.evaluate(facts, CONFIG).cover.status is status


@pytest.mark.parametrize(
    ("debit", "status"),
    [
        pytest.param("2026-05-24", CoverStatus.LAPSED, id="day-before-the-window"),
        pytest.param("2026-05-25", CoverStatus.ELIGIBLE, id="first-day-of-the-window"),
        pytest.param("2026-05-31", CoverStatus.ELIGIBLE, id="last-day-of-the-window"),
        pytest.param("2026-06-01", CoverStatus.ELIGIBLE, id="first-day-of-the-year"),
    ],
)
def test_a_debit_before_the_renewal_window_pays_for_the_year_that_is_ending(
    debit: str, status: CoverStatus
) -> None:
    assert pmjjby.evaluate(claim(premium(debit)), CONFIG).cover.status is status


@pytest.mark.parametrize(
    ("offset", "status"),
    [
        pytest.param(-1, CoverStatus.INELIGIBLE, id="lien-minus-one"),
        pytest.param(0, CoverStatus.ELIGIBLE, id="lien"),
        pytest.param(1, CoverStatus.ELIGIBLE, id="lien-plus-one"),
    ],
)
def test_natural_death_lien_covers_the_first_thirty_days(offset: int, status: CoverStatus) -> None:
    enrolled = d("2026-11-01")
    event = enrolled + timedelta(days=CONFIG.pmjjby.lien_days + offset)
    facts = replace(
        claim(premium(enrolled), event=EventType.NATURAL_DEATH), event_date=event, today=event
    )
    result = pmjjby.evaluate(facts, CONFIG)
    assert result.cover.status is status
    assert [f.code for f in result.flags] == ([] if offset >= 0 else ["death_within_lien_period"])


def test_natural_death_within_lien_period_is_not_payable() -> None:
    facts = replace(
        claim(premium("2026-06-20"), event=EventType.NATURAL_DEATH), event_date=d("2026-07-10")
    )
    result = pmjjby.evaluate(facts, CONFIG)
    assert result.cover.status is CoverStatus.INELIGIBLE
    assert result.cover.reasons[0].params == {"days_since_enrolment": 20, "lien_days": 30}
    assert [f.code for f in result.flags] == ["death_within_lien_period"]


def test_accident_within_lien_period_is_payable() -> None:
    facts = replace(claim(premium("2026-06-20")), event_date=d("2026-07-19"))
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_renewal_is_not_a_new_enrolment() -> None:
    facts = replace(
        claim(premium("2025-05-28"), premium("2026-05-28"), event=EventType.NATURAL_DEATH),
        event_date=d("2026-06-10"),
    )
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_a_premium_debited_after_the_event_does_not_insure_it() -> None:
    facts = claim(premium("2025-05-28"), premium("2026-11-20"))
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.LAPSED


def test_a_second_debit_later_in_the_year_keeps_the_cover_already_paid_for() -> None:
    cover = pmjjby.evaluate(claim(premium("2026-05-28"), premium("2026-11-20")), CONFIG).cover
    assert cover.status is CoverStatus.ELIGIBLE
    assert cover.evidence[0].date == d("2026-05-28")


@pytest.mark.parametrize("amount", [342, 228, 114])
def test_a_pro_rata_premium_insures_the_rest_of_the_cover_year(amount: int) -> None:
    facts = claim(premium("2026-09-01", amount))
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.ELIGIBLE


def test_a_premium_of_the_wrong_amount_is_not_cover() -> None:
    facts = claim(txn("2026-09-01", "PMJJBY PREMIUM", 435))
    assert pmjjby.evaluate(facts, CONFIG).cover.status is CoverStatus.NOT_FOUND


def test_a_credit_with_pmjjby_in_the_narration_is_not_a_premium() -> None:
    credit = txn("2026-05-28", "PMJJBY REVERSAL", 436, debit=False)
    assert pmjjby.evaluate(claim(credit), CONFIG).cover.status is CoverStatus.NOT_FOUND


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
