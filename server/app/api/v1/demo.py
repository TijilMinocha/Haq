from fastapi import APIRouter, status

from app.api.deps import ContainerDep, OptionalOperator
from app.schemas.case import CaseCreated
from app.schemas.meta import Scenario
from app.services.stub_scenarios import SCENARIOS

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios")
async def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS)


@router.post("/scenarios/{scenario_id}", status_code=status.HTTP_201_CREATED)
async def start_scenario(
    scenario_id: str, container: ContainerDep, operator: OptionalOperator
) -> CaseCreated:
    return await container.case_service.start_demo(scenario_id, operator.id if operator else None)
