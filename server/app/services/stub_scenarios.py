"""Seeded case inputs for the three demo scenarios.

Each fixture holds already-extracted documents; the real rules engine evaluates them. Phase 4
adds sample images that go through the mock extractor instead.
"""

import json
import re
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.models import CaseMode
from app.schemas.meta import Scenario

_DIR = Path(__file__).parent / "stubs"
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Dates of birth stay fixed: shifting them would change ages, not the story.
_FIXED_KEYS = frozenset({"date_of_birth", "as_of"})

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
def _raw(scenario_id: str) -> str | None:
    path = _DIR / f"{scenario_id}.json"
    if scenario_id not in {s.id for s in SCENARIOS} or not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _shift(value: Any, delta: timedelta, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: _shift(v, delta, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_shift(v, delta) for v in value]
    if isinstance(value, str) and key not in _FIXED_KEYS and _ISO_DATE.match(value):
        return (date.fromisoformat(value) + delta).isoformat()
    return value


def load_scenario(scenario_id: str, today: date | None = None) -> dict[str, Any] | None:
    """Loads a scenario with its dates moved so that `as_of` falls on `today`.

    This keeps day counts (deadlines, the RuPay 90-day window) the same on any demo day.
    Shifts of more than a few months would cross a cover-year boundary and change results.
    """
    raw = _raw(scenario_id)
    if raw is None:
        return None
    data: dict[str, Any] = json.loads(raw)
    delta = (today or date.today()) - date.fromisoformat(data["as_of"])
    shifted: dict[str, Any] = _shift(data, delta)
    return shifted
