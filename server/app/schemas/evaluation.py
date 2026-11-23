import datetime as dt
from typing import Any

from app.domain.models import CoverStatus, DocumentKind, FlagSeverity, Scheme
from app.schemas.common import ApiModel, Coded


class Evidence(ApiModel):
    date: dt.date
    narration: str
    amount: int


class CoverResult(ApiModel):
    scheme: Scheme
    status: CoverStatus
    amount: int
    evidence: list[Evidence] = []
    reasons: list[Coded] = []


class Flag(ApiModel):
    code: str
    severity: FlagSeverity
    params: dict[str, Any] = {}
    message: str


class ChecklistItem(ApiModel):
    scheme: Scheme
    document_kind: DocumentKind
    required: bool
    status: str


class Deadline(ApiModel):
    scheme: Scheme
    code: str
    due_date: dt.date
    days_left: int
    hard: bool


class Alert(ApiModel):
    code: str
    scheme: Scheme | None = None
    params: dict[str, Any] = {}
    message: str


class Evaluation(ApiModel):
    total_claimable: int = 0
    covers: list[CoverResult] = []
    flags: list[Flag] = []
    checklist: list[ChecklistItem] = []
    deadlines: list[Deadline] = []
    alerts: list[Alert] = []
