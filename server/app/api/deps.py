from typing import Annotated

from fastapi import Depends, Header, Path, Request

from app.core.errors import case_not_found, forbidden, invalid_token
from app.core.middleware import client_host
from app.core.security import decode_operator_jwt, token_matches
from app.infra.db.repositories import CaseRecord, OperatorRecord
from app.services.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]
ClientHost = Annotated[str, Depends(client_host)]


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


async def optional_operator(
    container: ContainerDep,
    authorization: Annotated[str | None, Header()] = None,
) -> OperatorRecord | None:
    token = _bearer(authorization)
    if token is None:
        return None
    operator_id = decode_operator_jwt(token)
    operator = await container.operators.get(operator_id) if operator_id else None
    if operator is None:
        raise invalid_token()
    return operator


OptionalOperator = Annotated[OperatorRecord | None, Depends(optional_operator)]


async def require_operator(operator: OptionalOperator) -> OperatorRecord:
    if operator is None:
        raise invalid_token()
    return operator


CurrentOperator = Annotated[OperatorRecord, Depends(require_operator)]


async def case_access(
    container: ContainerDep,
    operator: OptionalOperator,
    case_id: Annotated[str, Path()],
    x_case_token: Annotated[str | None, Header()] = None,
) -> CaseRecord:
    """A case opens with its own case token, or with the JWT of the operator who owns it."""
    if x_case_token is None and operator is None:
        raise invalid_token()
    record = await container.cases.get(case_id)
    if record is None:
        raise case_not_found()
    if x_case_token is not None:
        if token_matches(x_case_token, record.token_hashes):
            return record
        if operator is None:
            raise invalid_token()
    if operator is not None and record.owner_operator_id == operator.id:
        return record
    raise forbidden()


CaseDep = Annotated[CaseRecord, Depends(case_access)]
