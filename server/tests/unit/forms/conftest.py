from datetime import date
from typing import Any

import pytest

from app.schemas.case import CaseView
from app.services.evaluation_service import evaluate
from app.services.stub_scenarios import load_scenario

TODAY = date(2026, 11, 23)


def scenario_view(scenario_id: str, **changes: Any) -> CaseView:
    data = load_scenario(scenario_id, TODAY) or {}
    view = CaseView.model_validate(
        {
            **{
                k: data[k] for k in ("mode", "language", "subject", "event", "nominee", "documents")
            },
            "id": "c_test",
            "code": "HAQ-7K3P",
            "evaluation": {},
            "updated_at": "2026-11-23T00:00:00Z",
        }
    ).model_copy(update=changes)
    return view.model_copy(update={"evaluation": evaluate(view, TODAY)})


@pytest.fixture
def sunita() -> CaseView:
    return scenario_view("sunita_accident")
