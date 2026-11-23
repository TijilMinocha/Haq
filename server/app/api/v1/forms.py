from typing import Annotated, Any

from fastapi import APIRouter, Query, Response

from app.api.deps import CaseDep, ContainerDep
from app.domain.models import Scheme
from app.services import form_service

router = APIRouter(prefix="/cases/{case_id}", tags=["forms"])

_PDF: dict[str, Any] = {"content": {"application/pdf": {}}}


def _pdf(data: bytes, filename: str) -> Response:
    return Response(
        data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/forms/{scheme}", response_class=Response, responses={200: _PDF})
async def claim_form(scheme: Scheme, record: CaseDep, container: ContainerDep) -> Response:
    view = container.case_service.view(record)
    return _pdf(form_service.claim_form(view, scheme), f"{view.code}-{scheme}-claim.pdf")


@router.get("/letters/escalation", response_class=Response, responses={200: _PDF})
async def escalation_letter(
    scheme: Annotated[Scheme, Query()], record: CaseDep, container: ContainerDep
) -> Response:
    view = container.case_service.view(record)
    return _pdf(
        form_service.escalation_letter(view, scheme), f"{view.code}-{scheme}-escalation.pdf"
    )
