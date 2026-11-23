from dataclasses import dataclass
from typing import Protocol

from app.schemas.case import CaseView


@dataclass
class CaseRecord:
    view: CaseView
    pin_hash: str
    token_hashes: set[str]
    owner_operator_id: str | None
    scenario_id: str | None = None


@dataclass(frozen=True)
class OperatorRecord:
    id: str
    email: str
    name: str
    password_hash: str


class CaseRepository(Protocol):
    async def add(self, record: CaseRecord) -> None: ...
    async def get(self, case_id: str) -> CaseRecord | None: ...
    async def get_by_code(self, code: str) -> CaseRecord | None: ...
    async def save(self, record: CaseRecord) -> None: ...
    async def list_by_owner(self, operator_id: str) -> list[CaseRecord]: ...


class OperatorRepository(Protocol):
    async def add(self, record: OperatorRecord) -> None: ...
    async def get(self, operator_id: str) -> OperatorRecord | None: ...
    async def get_by_email(self, email: str) -> OperatorRecord | None: ...


class InMemoryCaseRepository:
    """Phase 1 stand-in; phase 3 replaces it with the Postgres repository."""

    def __init__(self) -> None:
        self._by_id: dict[str, CaseRecord] = {}

    async def add(self, record: CaseRecord) -> None:
        self._by_id[record.view.id] = record

    async def get(self, case_id: str) -> CaseRecord | None:
        return self._by_id.get(case_id)

    async def get_by_code(self, code: str) -> CaseRecord | None:
        return next((r for r in self._by_id.values() if r.view.code == code), None)

    async def save(self, record: CaseRecord) -> None:
        self._by_id[record.view.id] = record

    async def list_by_owner(self, operator_id: str) -> list[CaseRecord]:
        return [r for r in self._by_id.values() if r.owner_operator_id == operator_id]


class InMemoryOperatorRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, OperatorRecord] = {}

    async def add(self, record: OperatorRecord) -> None:
        self._by_id[record.id] = record

    async def get(self, operator_id: str) -> OperatorRecord | None:
        return self._by_id.get(operator_id)

    async def get_by_email(self, email: str) -> OperatorRecord | None:
        needle = email.strip().lower()
        return next((r for r in self._by_id.values() if r.email == needle), None)
