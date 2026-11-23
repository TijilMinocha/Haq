from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.domain.models import CoverStatus, DocumentKind, FlagSeverity, Scheme

Params = dict[str, Any]


@dataclass(frozen=True)
class Evidence:
    date: date
    narration: str
    amount: int


@dataclass(frozen=True)
class Reason:
    code: str
    params: Params = field(default_factory=dict)


@dataclass(frozen=True)
class Cover:
    scheme: Scheme
    status: CoverStatus
    amount: int
    evidence: tuple[Evidence, ...] = ()
    reasons: tuple[Reason, ...] = ()


@dataclass(frozen=True)
class Flag:
    code: str
    severity: FlagSeverity
    params: Params = field(default_factory=dict)


@dataclass(frozen=True)
class ChecklistItem:
    scheme: Scheme
    document_kind: DocumentKind
    required: bool
    received: bool


@dataclass(frozen=True)
class Deadline:
    scheme: Scheme
    code: str
    due_date: date
    days_left: int
    hard: bool


@dataclass(frozen=True)
class Alert:
    code: str
    scheme: Scheme | None = None
    params: Params = field(default_factory=dict)


@dataclass(frozen=True)
class SchemeResult:
    cover: Cover
    flags: tuple[Flag, ...] = ()
    deadlines: tuple[Deadline, ...] = ()
    alerts: tuple[Alert, ...] = ()


@dataclass(frozen=True)
class EvaluationResult:
    total_claimable: int
    covers: tuple[Cover, ...]
    flags: tuple[Flag, ...]
    checklist: tuple[ChecklistItem, ...]
    deadlines: tuple[Deadline, ...]
    alerts: tuple[Alert, ...]
