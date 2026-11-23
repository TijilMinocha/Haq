from dataclasses import dataclass

from app.core.attempts import AttemptLimiter
from app.core.config import Settings
from app.infra.db.repositories import (
    CaseRepository,
    InMemoryCaseRepository,
    InMemoryOperatorRepository,
    OperatorRepository,
)
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


def build_container(settings: Settings) -> Container:
    lock_seconds = settings.lockout_minutes * 60
    cases = InMemoryCaseRepository()
    operators = InMemoryOperatorRepository()
    case_service = CaseService(cases, AttemptLimiter(settings.lockout_attempts, lock_seconds))
    return Container(
        cases=cases,
        operators=operators,
        case_service=case_service,
        document_service=DocumentService(cases, case_service, settings.max_upload_mb),
        auth_service=AuthService(
            operators, AttemptLimiter(settings.lockout_attempts, lock_seconds)
        ),
    )
