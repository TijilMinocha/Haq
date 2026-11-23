"""Fixture CaseViews for the three demo scenarios (handoff v0).

Phase 4 replaces these with mock-extractor inputs run through the real rules engine.
"""

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.models import CaseMode
from app.schemas.evaluation import Evaluation
from app.schemas.meta import Scenario

_DIR = Path(__file__).parent / "stubs"

SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        id="sunita_accident",
        mode=CaseMode.CLAIM,
        title_code="scenario.sunita_accident",
        expected_total=600000,
    ),
    Scenario(
        id="meena_lien", mode=CaseMode.CLAIM, title_code="scenario.meena_lien", expected_total=0
    ),
    Scenario(
        id="raju_protect",
        mode=CaseMode.PROTECT,
        title_code="scenario.raju_protect",
        expected_total=0,
    ),
)


@lru_cache
def load_scenario(scenario_id: str) -> dict[str, Any] | None:
    path = _DIR / f"{scenario_id}.json"
    if scenario_id not in {s.id for s in SCENARIOS} or not path.exists():
        return None
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def refresh_days_left(evaluation: Evaluation, today: date) -> Evaluation:
    deadlines = [
        d.model_copy(update={"days_left": (d.due_date - today).days}) for d in evaluation.deadlines
    ]
    return evaluation.model_copy(update={"deadlines": deadlines})
