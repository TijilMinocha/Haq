from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import CaseDep, ContainerDep
from app.domain.models import DocumentKind
from app.schemas.case import CaseView
from app.schemas.document import DocumentPatch

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])


@router.post("")
async def upload_document(
    record: CaseDep,
    container: ContainerDep,
    kind: Annotated[DocumentKind, Form()],
    file: Annotated[UploadFile, File()],
) -> CaseView:
    content = await file.read()
    return await container.document_service.add(record, kind, content, file.content_type)


@router.patch("/{document_id}")
async def correct_document(
    document_id: str, body: DocumentPatch, record: CaseDep, container: ContainerDep
) -> CaseView:
    return await container.document_service.correct(record, document_id, body)


@router.delete("/{document_id}")
async def delete_document(document_id: str, record: CaseDep, container: ContainerDep) -> CaseView:
    return await container.document_service.delete(record, document_id)
