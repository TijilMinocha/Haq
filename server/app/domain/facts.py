"""Immutable inputs to the rules engine, built by the evaluation service from a case."""

from dataclasses import dataclass, field
from datetime import date

from app.domain.models import CaseMode, DocumentKind, EventType, TxnChannel


@dataclass(frozen=True)
class Txn:
    date: date
    narration: str
    amount: int
    is_debit: bool
    channel: TxnChannel = TxnChannel.OTHER


@dataclass(frozen=True)
class Passbook:
    document_id: str
    account_holder: str | None = None
    account_last4: str | None = None
    nominee_name: str | None = None
    card_bin: str | None = None
    card_issued_on: date | None = None
    transactions: tuple[Txn, ...] = ()


@dataclass(frozen=True)
class DocumentFacts:
    """The identity fields of one document, for cross-checks."""

    document_id: str
    kind: DocumentKind
    confidence: float
    corrected: bool
    name: str | None = None
    date_of_birth: date | None = None
    date_of_death: date | None = None


@dataclass(frozen=True)
class CaseFacts:
    mode: CaseMode
    today: date
    subject_name: str | None = None
    subject_dob: date | None = None
    event_type: EventType | None = None
    event_date: date | None = None
    nominee_name: str | None = None
    passbooks: tuple[Passbook, ...] = ()
    documents: tuple[DocumentFacts, ...] = ()
    kinds_present: frozenset[DocumentKind] = field(default_factory=frozenset)

    @property
    def passbook(self) -> Passbook | None:
        return self.passbooks[0] if self.passbooks else None

    @property
    def transactions(self) -> tuple[Txn, ...]:
        return tuple(t for p in self.passbooks for t in p.transactions)

    @property
    def is_accident(self) -> bool:
        return self.event_type in {EventType.ACCIDENTAL_DEATH, EventType.ACCIDENTAL_DISABILITY}

    @property
    def reference_date(self) -> date:
        """The day cover must have been in force: the event in claim mode, today otherwise."""
        if self.mode is CaseMode.CLAIM and self.event_date is not None:
            return self.event_date
        return self.today
