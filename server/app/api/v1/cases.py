from fastapi import APIRouter, status

from app.api.deps import CaseDep, ContainerDep, OptionalOperator
from app.schemas.case import CaseCreate, CaseCreated, CaseResume, CaseResumed, CaseUpdate, CaseView

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case(
    body: CaseCreate, container: ContainerDep, operator: OptionalOperator
) -> CaseCreated:
    return await container.case_service.create(body, operator.id if operator else None)


@router.post("/resume")
async def resume_case(body: CaseResume, container: ContainerDep) -> CaseResumed:
    return await container.case_service.resume(body)


@router.get("/{case_id}")
async def get_case(record: CaseDep, container: ContainerDep) -> CaseView:
    return container.case_service.view(record)


@router.patch("/{case_id}")
async def update_case(body: CaseUpdate, record: CaseDep, container: ContainerDep) -> CaseView:
    return await container.case_service.update(record, body)
