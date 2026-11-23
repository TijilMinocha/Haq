from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.attempts import AttemptStore, InMemoryAttemptStore
from app.core.config import Settings
from app.infra.db.engine import make_engine, make_sessions
from app.infra.db.postgres import (
    PostgresAttemptStore,
    PostgresCaseRepository,
    PostgresOperatorRepository,
)
from app.infra.db.repositories import (
    CaseRepository,
    InMemoryCaseRepository,
    InMemoryOperatorRepository,
    OperatorRepository,
)
from app.infra.extractors.base import Extractor
from app.infra.extractors.factory import build_extractor
from app.services.auth_service import AuthService
from app.services.case_service import CaseService
from app.services.document_service import DocumentService


@dataclass(frozen=True)
class Container:
    cases: CaseRepository
    operators: OperatorRepository
    case_service: CaseService
    document_service: DocumentService
    auth_service: AuthService
    engine: AsyncEngine | None = None

    async def close(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()


def build_container(settings: Settings, extractor: Extractor | None = None) -> Container:
    lock_seconds = settings.lockout_minutes * 60
    engine: AsyncEngine | None = None
    cases: CaseRepository
    operators: OperatorRepository
    case_attempts: AttemptStore
    login_attempts: AttemptStore

    if settings.storage == "postgres":
        engine = make_engine(settings.database_url)
        sessions = make_sessions(engine)
        cases = PostgresCaseRepository(sessions)
        operators = PostgresOperatorRepository(sessions)
        # One table serves both; case codes and emails cannot collide.
        case_attempts = login_attempts = PostgresAttemptStore(
            sessions, settings.lockout_attempts, lock_seconds
        )
    else:
        cases = InMemoryCaseRepository()
        operators = InMemoryOperatorRepository()
        case_attempts = InMemoryAttemptStore(settings.lockout_attempts, lock_seconds)
        login_attempts = InMemoryAttemptStore(settings.lockout_attempts, lock_seconds)

    case_service = CaseService(cases, case_attempts)
    return Container(
        cases=cases,
        operators=operators,
        case_service=case_service,
        document_service=DocumentService(
            cases, case_service, extractor or build_extractor(settings), settings.max_upload_mb
        ),
        auth_service=AuthService(operators, login_attempts),
        engine=engine,
    )
