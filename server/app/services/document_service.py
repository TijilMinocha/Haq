from datetime import UTC, datetime

from fastapi import UploadFile

from app.core.errors import AppError
from app.core.security import new_id
from app.domain.models import DocumentKind, DocumentStatus
from app.infra.db.repositories import CaseRecord, CaseRepository
from app.infra.extractors.base import Extractor, ExtractorUnavailable, UnreadableDocument
from app.infra.extractors.masking import mask_model
from app.infra.extractors.sniffing import sniff_type, too_many_pixels
from app.schemas.case import CaseView
from app.schemas.document import DocumentPatch, DocumentView, fields_model
from app.services.case_service import CaseService

_READ_CHUNK_BYTES = 64 * 1024


class DocumentService:
    def __init__(
        self,
        cases: CaseRepository,
        case_service: CaseService,
        extractor: Extractor,
        max_mb: int,
    ) -> None:
        self._cases = cases
        self._case_service = case_service
        self._extractor = extractor
        self._max_mb = max_mb
        self._max_bytes = max_mb * 1024 * 1024

    async def read_upload(self, upload: UploadFile) -> bytes:
        """Reads the body in bounded chunks, in case the declared length is missing or wrong."""
        chunks: list[bytes] = []
        total = 0
        while chunk := await upload.read(_READ_CHUNK_BYTES):
            total += len(chunk)
            if total > self._max_bytes:
                raise self._too_large()
            chunks.append(chunk)
        return b"".join(chunks)

    async def add(
        self, record: CaseRecord, kind: DocumentKind, content: bytes, content_type: str | None
    ) -> CaseView:
        if not content:
            raise self._unreadable(kind)
        if len(content) > self._max_bytes:
            raise self._too_large()
        # The declared type is only a hint: what the file really is decides how it is read.
        sniffed = sniff_type(content)
        if sniffed is None:
            raise AppError(
                "unsupported_file",
                415,
                "Use a JPEG, PNG, WebP or PDF file.",
                {"content_type": content_type},
            )
        if too_many_pixels(content):
            raise self._unreadable(kind)
        try:
            result = await self._extractor.extract(content, sniffed, kind)
        except UnreadableDocument as exc:
            raise self._unreadable(kind) from exc
        except ExtractorUnavailable as exc:
            raise AppError(
                "extractor_unavailable", 503, "Document reading is unavailable. Try again."
            ) from exc
        # Only the extracted fields live on; the uploaded bytes are dropped with this call.
        # Masking here as well as in the pipeline means no extractor can store a full number.
        fields = mask_model(fields_model(kind).model_validate(result.fields.model_dump()))
        document = DocumentView(
            id=new_id("d"),
            kind=kind,
            status=DocumentStatus.EXTRACTED,
            confidence=result.confidence,
            fields=fields,
        )
        return await self._replace_documents(record, [*record.view.documents, document])

    async def correct(self, record: CaseRecord, document_id: str, patch: DocumentPatch) -> CaseView:
        document = self._find(record, document_id)
        fields = mask_model(fields_model(document.kind).model_validate(patch.fields.model_dump()))
        updated = document.model_copy(update={"fields": fields, "status": DocumentStatus.CORRECTED})
        return await self._replace_documents(
            record, [updated if d.id == document_id else d for d in record.view.documents]
        )

    async def delete(self, record: CaseRecord, document_id: str) -> CaseView:
        self._find(record, document_id)
        return await self._replace_documents(
            record, [d for d in record.view.documents if d.id != document_id]
        )

    def _too_large(self) -> AppError:
        return AppError("file_too_large", 413, "File is too large.", {"max_mb": self._max_mb})

    def _unreadable(self, kind: DocumentKind) -> AppError:
        return AppError(
            "document_unreadable",
            422,
            "Could not read this document. Please retake the photo.",
            {"kind": kind.value},
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
