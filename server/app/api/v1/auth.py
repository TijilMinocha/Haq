from fastapi import APIRouter

from app.api.deps import ContainerDep, CurrentOperator
from app.schemas.auth import LoginRequest, LoginResponse, Operator
from app.services.auth_service import to_schema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, container: ContainerDep) -> LoginResponse:
    return await container.auth_service.login(body)


@router.get("/me")
async def me(operator: CurrentOperator) -> Operator:
    return to_schema(operator)
