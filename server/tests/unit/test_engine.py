from dataclasses import replace
from datetime import timedelta

import pytest

from app.domain.models import CoverStatus, DocumentKind, EventType, FlagSeverity, Scheme
from app.domain.rules.engine import evaluate

from .factories import (
    CONFIG,
    EVENT,
    TODAY,
    atm,
    claim,
    d,
    doc,
    passbook,
    pmjjby,
    pmsby,
    protect,
    with_docs,
)


def test_accident_stacks_all_three_covers() -> None:
    result = evaluate(claim(pmjjby(), pmsby(), atm("2026-10-30")), CONFIG)
    assert result.total_claimable == 600000
    assert [d.code for d in result.deadlines] == [
        "claim_submission",
        "claim_submission",
        "claim_intimation",
    ]


def test_accident_docs_missing_blocks_until_uploaded() -> None:
    facts = claim(pmjjby(), pmsby(), atm("2026-10-30"))
    (flag,) = [f for f in evaluate(facts, CONFIG).flags if f.code == "accident_docs_missing"]
    assert flag.params == {"missing": ["fir", "postmortem"]}
    done = with_docs(facts, doc(DocumentKind.FIR), doc(DocumentKind.POSTMORTEM))
    assert "accident_docs_missing" not in {f.code for f in evaluate(done, CONFIG).flags}


def test_no_accident_docs_needed_when_only_pmjjby_applies() -> None:
    result = evaluate(claim(pmjjby(), passbook=passbook(pmjjby(), card_bin=None)), CONFIG)
    assert "accident_docs_missing" not in {f.code for f in result.flags}


def test_checklist_marks_received_documents() -> None:
    facts = with_docs(claim(pmjjby()), doc(DocumentKind.DEATH_CERTIFICATE, name="Ramesh Kumar"))
    items = {
        (i.scheme.value, i.document_kind): i.received for i in evaluate(facts, CONFIG).checklist
    }
    assert items[("PMJJBY", DocumentKind.DEATH_CERTIFICATE)] is True
    assert items[("PMJJBY", DocumentKind.AADHAAR_NOMINEE)] is False


def test_claim_window_closing() -> None:
    facts = replace(claim(pmjjby()), today=d("2026-12-10"))
    (flag,) = [f for f in evaluate(facts, CONFIG).flags if f.code == "claim_window_closing"]
    assert flag.params["days_left"] == 5


def test_claim_window_passed() -> None:
    facts = replace(claim(pmjjby()), today=d("2026-12-20"))
    (flag,) = [f for f in evaluate(facts, CONFIG).flags if f.code == "claim_window_passed"]
    assert flag.params["days_late"] == 5


@pytest.mark.parametrize(
    ("offset", "days_left", "flag"),
    [
        pytest.param(0, 0, "claim_window_closing", id="on-the-due-date"),
        pytest.param(1, -1, "claim_window_passed", id="day-after-the-due-date"),
    ],
)
def test_deadline_days_left_counts_from_the_due_date(
    offset: int, days_left: int, flag: str
) -> None:
    due = EVENT + timedelta(days=CONFIG.pmjjby.claim_preferred_within_days)
    result = evaluate(replace(claim(pmjjby()), today=due + timedelta(days=offset)), CONFIG)
    (submission,) = [x for x in result.deadlines if x.scheme is Scheme.PMJJBY]
    assert (submission.due_date, submission.days_left) == (due, days_left)
    (raised,) = [f for f in result.flags if f.code == flag]
    assert raised.params["days_left" if days_left >= 0 else "days_late"] == abs(days_left)


def test_total_claimable_counts_every_live_status() -> None:
    facts = claim(pmjjby(), pmsby(), atm("2026-10-30"), event=EventType.ACCIDENTAL_DISABILITY)
    result = evaluate(facts, CONFIG)
    assert {c.scheme.value: c.status for c in result.covers} == {
        "PMJJBY": CoverStatus.INELIGIBLE,
        "PMSBY": CoverStatus.NEEDS_VERIFICATION,
        "RUPAY_PMJDY": CoverStatus.LIKELY_ELIGIBLE,
    }
    assert result.total_claimable == (
        CONFIG.pmsby.death_or_total_disability + CONFIG.rupay.new_card_amount
    )


def test_total_claimable_ignores_lapsed_and_ineligible_covers() -> None:
    facts = claim(pmjjby("2025-05-29"), pmsby("2025-05-30"), atm("2026-01-01"))
    assert evaluate(facts, CONFIG).total_claimable == 0


def test_flags_sorted_blockers_first_and_deduplicated() -> None:
    facts = with_docs(
        claim(pmjjby(), pmsby(), atm("2026-10-30")),
        doc(DocumentKind.DEATH_CERTIFICATE, name="Rames Kumar"),
        doc(DocumentKind.AADHAAR_DECEASED, confidence=0.2),
    )
    flags = evaluate(facts, CONFIG).flags
    severities = [f.severity for f in flags]
    assert severities == sorted(
        severities, key=[FlagSeverity.BLOCKER, FlagSeverity.WARNING, FlagSeverity.INFO].index
    )
    assert len({(f.code, repr(f.params)) for f in flags}) == len(flags)


def test_natural_death_counts_only_pmjjby() -> None:
    result = evaluate(
        claim(pmjjby(), pmsby(), atm("2026-10-30"), event=EventType.NATURAL_DEATH), CONFIG
    )
    assert result.total_claimable == CONFIG.pmjjby.sum_assured
    statuses = {c.scheme.value: c.status for c in result.covers}
    assert statuses["PMJJBY"] is CoverStatus.ELIGIBLE
    assert statuses["PMSBY"] is CoverStatus.INELIGIBLE
    assert statuses["RUPAY_PMJDY"] is CoverStatus.INELIGIBLE


def test_protect_mode_has_no_claim_total_and_orders_alerts() -> None:
    facts = protect(
        pmjjby("2025-05-29"),
        pmsby(),
        atm("2026-09-06"),
        passbook=passbook(pmjjby("2025-05-29"), pmsby(), atm("2026-09-06"), nominee_name=None),
    )
    result = evaluate(facts, CONFIG)
    assert result.total_claimable == 0
    assert result.checklist == ()
    codes = [a.code for a in result.alerts]
    assert set(codes) == {
        "alert.cover_lapsed",
        "alert.rupay_expiring",
        "alert.nominee_missing",
        "alert.cover_active",
    }
    assert codes[-1] == "alert.cover_active"
    assert facts.today == TODAY
