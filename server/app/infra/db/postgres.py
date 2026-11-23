from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import too_many_attempts
from app.domain.models import CaseMode, Language
from app.infra.db.models import AuthFailureRow, CaseRow, CaseTokenRow, DocumentRow, OperatorRow
from app.infra.db.repositories import CaseRecord, OperatorRecord
from app.schemas.case import CaseView, Event, Nominee, Subject
from app.schemas.document import DocumentView
from app.schemas.evaluation import Evaluation

Sessions = async_sessionmaker[AsyncSession]


def _to_record(row: CaseRow) -> CaseRecord:
    view = CaseView(
        id=row.id,
        code=row.code,
        mode=CaseMode(row.mode),
        language=Language(row.language),
        subject=Subject.model_validate(row.subject),
        event=Event.model_validate(row.event),
        nominee=Nominee.model_validate(row.nominee),
        documents=[
            DocumentView.model_validate(
                {
                    "id": d.id,
                    "kind": d.kind,
                    "status": d.status,
                    "confidence": d.confidence,
                    "fields": d.fields,
                }
            )
            for d in row.documents
        ],
        # Evaluation is never stored: the service recomputes it from the facts on every read.
        evaluation=Evaluation(),
        updated_at=row.updated_at,
    )
    return CaseRecord(
        view=view,
        pin_hash=row.pin_hash,
        token_hashes={t.token_hash for t in row.tokens},
        owner_operator_id=row.owner_operator_id,
        scenario_id=row.scenario_id,
    )


def _apply(row: CaseRow, record: CaseRecord) -> None:
    view = record.view
    row.code = view.code
    row.mode = view.mode.value
    row.language = view.language.value
    row.subject = view.subject.model_dump(mode="json")
    row.event = view.event.model_dump(mode="json")
    row.nominee = view.nominee.model_dump(mode="json")
    row.pin_hash = record.pin_hash
    row.owner_operator_id = record.owner_operator_id
    row.scenario_id = record.scenario_id
    row.updated_at = view.updated_at

    existing = {d.id: d for d in row.documents}
    documents = []
    for position, doc in enumerate(view.documents):
        doc_row = existing.get(doc.id) or DocumentRow(id=doc.id)
        doc_row.position = position
        doc_row.kind = doc.kind.value
        doc_row.status = doc.status.value
        doc_row.confidence = doc.confidence
        doc_row.fields = doc.fields.model_dump(mode="json")
        documents.append(doc_row)
    row.documents = documents

    known = {t.token_hash for t in row.tokens}
    row.tokens.extend(CaseTokenRow(token_hash=h) for h in record.token_hashes - known)


class PostgresCaseRepository:
    def __init__(self, sessions: Sessions) -> None:
        self._sessions = sessions

    async def add(self, record: CaseRecord) -> None:
        async with self._sessions.begin() as session:
            row = CaseRow(id=record.view.id, documents=[], tokens=[])
            _apply(row, record)
            session.add(row)

    async def get(self, case_id: str) -> CaseRecord | None:
        async with self._sessions() as session:
            row = await session.get(CaseRow, case_id)
            return _to_record(row) if row else None

    async def get_by_code(self, code: str) -> CaseRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(select(CaseRow).where(CaseRow.code == code))
            return _to_record(row) if row else None

    async def save(self, record: CaseRecord) -> None:
        async with self._sessions.begin() as session:
            row = await session.get(CaseRow, record.view.id)
            if row is None:
                row = CaseRow(id=record.view.id, documents=[], tokens=[])
                session.add(row)
            _apply(row, record)

    async def list_by_owner(self, operator_id: str) -> list[CaseRecord]:
        async with self._sessions() as session:
            rows = await session.scalars(
                select(CaseRow)
                .where(CaseRow.owner_operator_id == operator_id)
                .order_by(CaseRow.updated_at.desc())
            )
            return [_to_record(r) for r in rows]


class PostgresOperatorRepository:
    def __init__(self, sessions: Sessions) -> None:
        self._sessions = sessions

    async def add(self, record: OperatorRecord) -> None:
        async with self._sessions.begin() as session:
            session.add(
                OperatorRow(
                    id=record.id,
                    email=record.email.strip().lower(),
                    name=record.name,
                    password_hash=record.password_hash,
                )
            )

    async def get(self, operator_id: str) -> OperatorRecord | None:
        async with self._sessions() as session:
            row = await session.get(OperatorRow, operator_id)
            return _operator(row) if row else None

    async def get_by_email(self, email: str) -> OperatorRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(OperatorRow).where(OperatorRow.email == email.strip().lower())
            )
            return _operator(row) if row else None


def _operator(row: OperatorRow) -> OperatorRecord:
    return OperatorRecord(
        id=row.id, email=row.email, name=row.name, password_hash=row.password_hash
    )


class PostgresAttemptStore:
    def __init__(self, sessions: Sessions, max_attempts: int, lock_seconds: int) -> None:
        self._sessions = sessions
        self._max_attempts = max_attempts
        self._lock_seconds = lock_seconds

    def _cutoff(self) -> datetime:
        return datetime.now(UTC) - timedelta(seconds=self._lock_seconds)

    async def check(self, key: str) -> None:
        async with self._sessions() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(AuthFailureRow)
                .where(AuthFailureRow.key == key, AuthFailureRow.failed_at > self._cutoff())
            )
        if (count or 0) >= self._max_attempts:
            raise too_many_attempts(self._lock_seconds // 60)

    async def fail(self, key: str) -> None:
        async with self._sessions.begin() as session:
            # Old failures no longer count, so prune them while we are here.
            await session.execute(
                delete(AuthFailureRow).where(
                    AuthFailureRow.key == key, AuthFailureRow.failed_at <= self._cutoff()
                )
            )
            session.add(AuthFailureRow(key=key, failed_at=datetime.now(UTC)))

    async def reset(self, key: str) -> None:
        async with self._sessions.begin() as session:
            await session.execute(delete(AuthFailureRow).where(AuthFailureRow.key == key))
