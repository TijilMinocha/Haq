from datetime import date
from typing import Any

import pytest

from app.schemas.case import CaseView
from app.services.evaluation_service import evaluate
from app.services.stub_scenarios import load_scenario

# The demo may run on any day; shifted fixtures must tell the same story.
DEMO_DAYS = [date(2026, 11, 23), date(2026, 12, 20), date(2027, 2, 10)]


def _view(scenario_id: str, today: date) -> CaseView:
    data: dict[str, Any] = load_scenario(scenario_id, today) or {}
    return CaseView.model_validate(
        {
            **{
                k: data[k] for k in ("mode", "language", "subject", "event", "nominee", "documents")
            },
            "id": "c_test",
            "code": "HAQ-TEST",
            "evaluation": {},
            "updated_at": "2026-11-23T00:00:00Z",
        }
    )


@pytest.mark.parametrize("today", DEMO_DAYS)
def test_sunita(today: date) -> None:
    result = evaluate(_view("sunita_accident", today), today)
    assert result.total_claimable == 600000
    assert [f.code for f in result.flags if f.severity == "blocker"] == [
        "name_mismatch",
        "accident_docs_missing",
    ]
    assert {i.document_kind.value for i in result.checklist if i.status == "missing"} >= {"fir"}
    assert [d.days_left for d in result.deadlines] == [22, 22, 82]


@pytest.mark.parametrize("today", DEMO_DAYS)
def test_meena(today: date) -> None:
    result = evaluate(_view("meena_lien", today), today)
    assert result.total_claimable == 0
    covers = {c.scheme.value: c for c in result.covers}
    assert covers["PMJJBY"].status == "ineligible"
    assert covers["PMJJBY"].reasons[0].code == "death_within_lien_period"
    assert [f.code for f in result.flags] == ["death_within_lien_period"]


@pytest.mark.parametrize("today", DEMO_DAYS)
def test_raju(today: date) -> None:
    result = evaluate(_view("raju_protect", today), today)
    alerts = {a.code: a.params for a in result.alerts}
    assert set(alerts) == {
        "alert.cover_lapsed",
        "alert.rupay_expiring",
        "alert.nominee_missing",
        "alert.cover_active",
    }
    assert alerts["alert.rupay_expiring"]["days_left"] == 12
