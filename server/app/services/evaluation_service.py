from datetime import date

from app.infra.db.repositories import CaseRecord
from app.schemas.evaluation import Evaluation
from app.services.stub_scenarios import load_scenario, refresh_days_left


def evaluate(record: CaseRecord, today: date | None = None) -> Evaluation:
    """Stub until phase 2: demo cases replay their fixture, other cases are empty."""
    today = today or date.today()
    if record.scenario_id:
        fixture = load_scenario(record.scenario_id)
        if fixture is not None:
            return refresh_days_left(Evaluation.model_validate(fixture["evaluation"]), today)
    return Evaluation()
