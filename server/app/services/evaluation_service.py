"""Builds rule-engine facts from a case and maps the engine's results back to the API schema."""

from datetime import date

from app.domain.config.loader import load_config
from app.domain.facts import CaseFacts, DocumentFacts, Passbook, Txn
from app.domain.models import DocumentStatus
from app.domain.results import EvaluationResult
from app.domain.rules.engine import evaluate as run_engine
from app.schemas import evaluation as api
from app.schemas.case import CaseView
from app.schemas.common import Coded
from app.schemas.document import (
    DeathCertificateFields,
    DocumentFields,
    DocumentView,
    GenericFields,
    IdentityFields,
    PassbookFields,
)
from app.services.messages import message_for


def _passbook(doc: DocumentView, fields: PassbookFields) -> Passbook:
    return Passbook(
        document_id=doc.id,
        account_holder=fields.account_holder,
        account_last4=fields.account_last4,
        nominee_name=fields.nominee_name,
        card_bin=fields.card_bin,
        card_issued_on=fields.card_issued_on,
        transactions=tuple(
            Txn(
                date=t.date,
                narration=t.narration,
                amount=t.amount,
                is_debit=t.direction == "debit",
                channel=t.channel,
            )
            for t in fields.transactions
        ),
    )


def _identity(fields: DocumentFields) -> tuple[str | None, date | None, date | None]:
    """Name, date of birth and date of death, where the document kind carries them."""
    match fields:
        case PassbookFields():
            return fields.account_holder, None, None
        case DeathCertificateFields():
            return fields.deceased_name, fields.date_of_birth, fields.date_of_death
        case IdentityFields():
            return fields.name, fields.date_of_birth, None
        case GenericFields():
            return fields.name, None, None


def _document(doc: DocumentView) -> DocumentFacts:
    name, dob, dod = _identity(doc.fields)
    return DocumentFacts(
        document_id=doc.id,
        kind=doc.kind,
        confidence=doc.confidence,
        corrected=doc.status is DocumentStatus.CORRECTED,
        name=name,
        date_of_birth=dob,
        date_of_death=dod,
    )


def build_facts(view: CaseView, today: date) -> CaseFacts:
    readable = [d for d in view.documents if d.status is not DocumentStatus.UNREADABLE]
    return CaseFacts(
        mode=view.mode,
        today=today,
        subject_name=view.subject.name,
        subject_dob=view.subject.date_of_birth,
        event_type=view.event.type,
        event_date=view.event.date,
        nominee_name=view.nominee.name,
        passbooks=tuple(
            _passbook(d, d.fields) for d in readable if isinstance(d.fields, PassbookFields)
        ),
        documents=tuple(_document(d) for d in readable),
        kinds_present=frozenset(d.kind for d in readable),
    )


def to_schema(result: EvaluationResult) -> api.Evaluation:
    return api.Evaluation(
        total_claimable=result.total_claimable,
        covers=[
            api.CoverResult(
                scheme=c.scheme,
                status=c.status,
                amount=c.amount,
                evidence=[
                    api.Evidence(date=e.date, narration=e.narration, amount=e.amount)
                    for e in c.evidence
                ],
                reasons=[Coded(code=r.code, params=r.params) for r in c.reasons],
            )
            for c in result.covers
        ],
        flags=[
            api.Flag(
                code=f.code,
                severity=f.severity,
                params=f.params,
                message=message_for(f.code, f.params),
            )
            for f in result.flags
        ],
        checklist=[
            api.ChecklistItem(
                scheme=i.scheme,
                document_kind=i.document_kind,
                required=i.required,
                status="received" if i.received else "missing",
            )
            for i in result.checklist
        ],
        deadlines=[
            api.Deadline(
                scheme=d.scheme,
                code=d.code,
                due_date=d.due_date,
                days_left=d.days_left,
                hard=d.hard,
            )
            for d in result.deadlines
        ],
        alerts=[
            api.Alert(
                code=a.code, scheme=a.scheme, params=a.params, message=message_for(a.code, a.params)
            )
            for a in result.alerts
        ],
    )


def evaluate(view: CaseView, today: date | None = None) -> api.Evaluation:
    facts = build_facts(view, today or date.today())
    return to_schema(run_engine(facts, load_config()))
