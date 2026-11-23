"""Collects everything a claim form or letter prints, from the case and its evaluation."""

from dataclasses import dataclass
from datetime import date

from app.domain.models import DocumentKind, EventType, FlagSeverity, Scheme
from app.schemas.case import CaseView
from app.schemas.document import (
    CardFields,
    DeathCertificateFields,
    GenericFields,
    PassbookFields,
)
from app.schemas.evaluation import CoverResult, Deadline
from app.services.forms.blockers import describe
from app.services.forms.labels import (
    DOCUMENT_NAMES,
    EVENT_NAMES,
    RELATIONS_HI,
    SCHEME_NAMES,
)


def format_inr(rupees: int) -> str:
    """Indian digit grouping: 600000 -> ₹6,00,000."""
    digits = str(abs(rupees))
    head, tail = digits[:-3], digits[-3:]
    groups: list[str] = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return "₹" + ",".join([*groups, tail])


# Official forms ask for the cause in a word, not the event description.
_CAUSES = {
    EventType.NATURAL_DEATH: "Natural causes",
    EventType.ACCIDENTAL_DEATH: "Accident",
    EventType.ACCIDENTAL_DISABILITY: "Accident",
}


def format_date(day: date | None) -> str | None:
    return day.strftime("%d-%m-%Y") if day else None


@dataclass(frozen=True)
class Bilingual:
    en: str
    hi: str


@dataclass(frozen=True)
class EvidenceLine:
    date: str
    narration: str
    amount: str


@dataclass(frozen=True)
class DocumentLine:
    name: Bilingual
    received: bool


@dataclass(frozen=True)
class FormData:
    scheme: Scheme
    scheme_name: Bilingual
    case_code: str
    prepared_on: str
    claim_amount: str
    is_death: bool
    insured_name: str | None
    insured_dob: str | None
    insured_age: int | None
    account: str | None
    bank: str | None
    branch: str | None
    ifsc: str | None
    event: Bilingual | None
    event_date: str | None
    event_weekday: str | None
    cause: str | None
    has_death_certificate: bool
    place: str | None
    death_registration: str | None
    fir_number: str | None
    postmortem_number: str | None
    claimant_name: str | None
    claimant_relation: Bilingual | None
    nominee_missing: bool
    card: str | None
    card_last_use: str | None
    evidence: tuple[EvidenceLine, ...]
    documents: tuple[DocumentLine, ...]
    blockers: tuple[Bilingual, ...]
    deadline: Deadline | None
    deadline_date: str | None


def _first[T](view: CaseView, kind: type[T]) -> T | None:
    return next((d.fields for d in view.documents if isinstance(d.fields, kind)), None)


def _generic(view: CaseView, kind: DocumentKind) -> GenericFields | None:
    for doc in view.documents:
        if doc.kind is kind and isinstance(doc.fields, GenericFields):
            return doc.fields
    return None


def build(view: CaseView, cover: CoverResult) -> FormData:
    scheme = cover.scheme
    passbook = _first(view, PassbookFields)
    certificate = _first(view, DeathCertificateFields)
    card = _first(view, CardFields)
    fir = _generic(view, DocumentKind.FIR)
    postmortem = _generic(view, DocumentKind.POSTMORTEM)
    is_death = view.event.type in {EventType.NATURAL_DEATH, EventType.ACCIDENTAL_DEATH}

    if is_death:
        claimant = view.nominee.name or (passbook.nominee_name if passbook else None)
        relation = view.nominee.relation
    else:
        claimant, relation = view.subject.name, None
    relation_text = (
        Bilingual(relation.title(), RELATIONS_HI.get(relation.lower(), relation))
        if relation
        else None
    )

    deadline = next((d for d in view.evaluation.deadlines if d.scheme == scheme), None)
    account_last4 = passbook.account_last4 if passbook else None
    card_text = None
    if card and card.card_bin and card.card_last4:
        card_text = f"{card.card_bin[:4]} {card.card_bin[4:]}XX XXXX {card.card_last4}"
    elif passbook and passbook.card_bin:
        # The insurer identifies PMJDY cards by their first 6 digits; the rest stays masked.
        card_text = f"{passbook.card_bin[:4]} {passbook.card_bin[4:]}XX XXXX XXXX"

    return FormData(
        scheme=scheme,
        scheme_name=Bilingual(*SCHEME_NAMES[scheme]),
        case_code=view.code,
        prepared_on=format_date(date.today()) or "",
        claim_amount=format_inr(cover.amount),
        is_death=is_death,
        insured_name=view.subject.name or (passbook.account_holder if passbook else None),
        insured_dob=format_date(view.subject.date_of_birth),
        insured_age=certificate.age if certificate else None,
        # Only the last 4 digits are ever stored; the bank fills in the full number.
        account=f"XXXXXXXX{account_last4}" if account_last4 else None,
        bank=passbook.bank if passbook else None,
        branch=passbook.branch if passbook else None,
        ifsc=passbook.ifsc if passbook else None,
        event=Bilingual(*EVENT_NAMES[view.event.type]) if view.event.type else None,
        event_date=format_date(view.event.date),
        event_weekday=view.event.date.strftime("%A") if view.event.date else None,
        cause=_CAUSES.get(view.event.type) if view.event.type else None,
        has_death_certificate=certificate is not None,
        place=certificate.place_of_death if certificate else None,
        death_registration=certificate.registration_number if certificate else None,
        fir_number=fir.reference_number if fir else None,
        postmortem_number=postmortem.reference_number if postmortem else None,
        claimant_name=claimant,
        claimant_relation=relation_text,
        nominee_missing=is_death and not claimant,
        card=card_text,
        card_last_use=format_date(cover.evidence[-1].date)
        if scheme is Scheme.RUPAY_PMJDY and cover.evidence
        else None,
        evidence=tuple(
            EvidenceLine(format_date(e.date) or "", e.narration, format_inr(e.amount))
            for e in cover.evidence
        ),
        documents=tuple(
            DocumentLine(Bilingual(*DOCUMENT_NAMES[i.document_kind]), i.status == "received")
            for i in view.evaluation.checklist
            if i.scheme == scheme
        ),
        blockers=tuple(
            Bilingual(*describe(f))
            for f in view.evaluation.flags
            if f.severity is FlagSeverity.BLOCKER
        ),
        deadline=deadline,
        deadline_date=format_date(deadline.due_date) if deadline else None,
    )
