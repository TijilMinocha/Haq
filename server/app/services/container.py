from dataclasses import dataclass

from sqlalchemy import text
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
from app.services.case_service import IP_ATTEMPT_FACTOR, CaseService
from app.services.document_service import DocumentService


@dataclass(frozen=True)
class Container:
    cases: CaseRepository
    operators: OperatorRepository
    case_service: CaseService
    document_service: DocumentService
    auth_service: AuthService
    extractor: Extractor | None = None
    engine: AsyncEngine | None = None

    async def database_ready(self) -> bool:
        if self.engine is None:
            return True
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            # Any failure means not ready; the details are in the database driver's log.
            return False
        return True

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
    resume_ip_attempts: AttemptStore
    ip_attempts = settings.lockout_attempts * IP_ATTEMPT_FACTOR

    if settings.storage == "postgres":
        engine = make_engine(settings.database_url)
        sessions = make_sessions(engine)
        cases = PostgresCaseRepository(sessions)
        operators = PostgresOperatorRepository(sessions)
        # One table serves all three; case codes, emails and ip keys cannot collide because
        # the resume keys carry a prefix.
        case_attempts = PostgresAttemptStore(sessions, settings.lockout_attempts, lock_seconds)
        login_attempts = PostgresAttemptStore(sessions, settings.lockout_attempts, lock_seconds)
        resume_ip_attempts = PostgresAttemptStore(sessions, ip_attempts, lock_seconds)
    else:
        cases = InMemoryCaseRepository()
        operators = InMemoryOperatorRepository()
        case_attempts = InMemoryAttemptStore(settings.lockout_attempts, lock_seconds)
        login_attempts = InMemoryAttemptStore(settings.lockout_attempts, lock_seconds)
        resume_ip_attempts = InMemoryAttemptStore(ip_attempts, lock_seconds)

    case_service = CaseService(cases, case_attempts, resume_ip_attempts)
    reader = extractor or build_extractor(settings)
    return Container(
        cases=cases,
        operators=operators,
        case_service=case_service,
        document_service=DocumentService(cases, case_service, reader, settings.max_upload_mb),
        auth_service=AuthService(operators, login_attempts, settings.seed_password),
        extractor=reader,
        engine=engine,
    )
