from datetime import UTC, datetime

from app.core.errors import AppError
from app.core.security import new_id
from app.domain.models import DocumentKind, DocumentStatus
from app.infra.db.repositories import CaseRecord, CaseRepository
from app.schemas.case import CaseView
from app.schemas.document import (
    DeathCertificateFields,
    DocumentFields,
    DocumentPatch,
    DocumentView,
    GenericFields,
    IdentityFields,
    PassbookFields,
)
from app.services.case_service import CaseService

ALLOWED_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "application/pdf"})

_FIELDS_BY_KIND: dict[DocumentKind, type[DocumentFields]] = {
    DocumentKind.PASSBOOK: PassbookFields,
    DocumentKind.DEATH_CERTIFICATE: DeathCertificateFields,
    DocumentKind.AADHAAR_DECEASED: IdentityFields,
    DocumentKind.AADHAAR_NOMINEE: IdentityFields,
}


def fields_model(kind: DocumentKind) -> type[DocumentFields]:
    return _FIELDS_BY_KIND.get(kind, GenericFields)


class DocumentService:
    def __init__(self, cases: CaseRepository, case_service: CaseService, max_mb: int) -> None:
        self._cases = cases
        self._case_service = case_service
        self._max_bytes = max_mb * 1024 * 1024

    async def add(
        self, record: CaseRecord, kind: DocumentKind, content: bytes, content_type: str | None
    ) -> CaseView:
        if content_type not in ALLOWED_TYPES:
            raise AppError(
                "unsupported_file",
                415,
                "Use a JPEG, PNG, WebP or PDF file.",
                {"content_type": content_type},
            )
        if len(content) > self._max_bytes:
            raise AppError(
                "file_too_large",
                413,
                "File is too large.",
                {"max_mb": self._max_bytes // (1024 * 1024)},
            )
        # The bytes go no further than this call; extraction arrives in phase 4.
        document = DocumentView(
            id=new_id("d"),
            kind=kind,
            status=DocumentStatus.EXTRACTED,
            confidence=0.0,
            fields=fields_model(kind)(),
        )
        return await self._replace_documents(record, [*record.view.documents, document])

    async def correct(self, record: CaseRecord, document_id: str, patch: DocumentPatch) -> CaseView:
        document = self._find(record, document_id)
        fields = fields_model(document.kind).model_validate(patch.fields.model_dump())
        updated = document.model_copy(update={"fields": fields, "status": DocumentStatus.CORRECTED})
        return await self._replace_documents(
            record, [updated if d.id == document_id else d for d in record.view.documents]
        )

    async def delete(self, record: CaseRecord, document_id: str) -> CaseView:
        self._find(record, document_id)
        return await self._replace_documents(
            record, [d for d in record.view.documents if d.id != document_id]
        )

    async def _replace_documents(
        self, record: CaseRecord, documents: list[DocumentView]
    ) -> CaseView:
        record.view = record.view.model_copy(
            update={"documents": documents, "updated_at": datetime.now(UTC)}
        )
        await self._cases.save(record)
        return self._case_service.view(record)

    @staticmethod
    def _find(record: CaseRecord, document_id: str) -> DocumentView:
        for document in record.view.documents:
            if document.id == document_id:
                return document
        raise AppError("document_not_found", 404, "Document not found.")
