from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ContainerDep, CurrentOperator
from app.schemas.case import CaseSummary

router = APIRouter(prefix="/operator", tags=["operator"])


@router.get("/cases")
async def list_cases(
    container: ContainerDep,
    operator: CurrentOperator,
    status: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> list[CaseSummary]:
    return await container.case_service.list_for_operator(operator.id, status, q)
