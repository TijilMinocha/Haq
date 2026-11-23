from dataclasses import replace
from datetime import date
from typing import Any

from app.domain.config.loader import load_config
from app.domain.facts import CaseFacts, DocumentFacts, Passbook, Txn
from app.domain.models import CaseMode, DocumentKind, EventType, TxnChannel

CONFIG = load_config()
TODAY = date(2026, 11, 23)
EVENT = date(2026, 11, 15)

PMJJBY_RENEWAL = date(2026, 5, 28)
PMSBY_RENEWAL = date(2026, 5, 30)


def d(iso: str) -> date:
    return date.fromisoformat(iso)


def txn(
    day: date | str,
    narration: str,
    amount: int,
    *,
    debit: bool = True,
    channel: TxnChannel = TxnChannel.OTHER,
) -> Txn:
    return Txn(d(day) if isinstance(day, str) else day, narration, amount, debit, channel)


def pmjjby(day: date | str = PMJJBY_RENEWAL, amount: int = 436) -> Txn:
    return txn(day, "PMJJBY PREMIUM", amount)


def pmsby(day: date | str = PMSBY_RENEWAL) -> Txn:
    return txn(day, "PMSBY PREMIUM", 20)


def atm(day: date | str) -> Txn:
    return txn(day, "ATM WDL SEELAMPUR", 2000)


def passbook(*txns: Txn, **kwargs: Any) -> Passbook:
    defaults: dict[str, Any] = {
        "document_id": "d_pb",
        "account_holder": "Ramesh Kumar",
        "account_last4": "4417",
        "nominee_name": "Sunita Devi",
        "card_bin": "607392",
        "card_issued_on": d("2019-02-11"),
    }
    return Passbook(**{**defaults, **kwargs}, transactions=txns)


def doc(kind: DocumentKind, **kwargs: Any) -> DocumentFacts:
    defaults: dict[str, Any] = {
        "document_id": f"d_{kind.value}",
        "kind": kind,
        "confidence": 0.9,
        "corrected": False,
    }
    return DocumentFacts(**{**defaults, **kwargs})


def claim(
    *txns: Txn, event: EventType | None = EventType.ACCIDENTAL_DEATH, **kwargs: Any
) -> CaseFacts:
    pb = kwargs.pop("passbook", None) or passbook(*txns)
    facts = CaseFacts(
        mode=CaseMode.CLAIM,
        today=TODAY,
        subject_name="Ramesh Kumar",
        event_type=event,
        event_date=EVENT if event else None,
        nominee_name="Sunita Devi",
        passbooks=(pb,),
        documents=(doc(DocumentKind.PASSBOOK, name=pb.account_holder),),
        kinds_present=frozenset({DocumentKind.PASSBOOK}),
    )
    return replace(facts, **kwargs)


def protect(*txns: Txn, **kwargs: Any) -> CaseFacts:
    pb = kwargs.pop("passbook", None) or passbook(*txns)
    facts = CaseFacts(
        mode=CaseMode.PROTECT,
        today=TODAY,
        subject_name="Raju Prasad",
        passbooks=(pb,),
        documents=(doc(DocumentKind.PASSBOOK, name=pb.account_holder),),
        kinds_present=frozenset({DocumentKind.PASSBOOK}),
    )
    return replace(facts, **kwargs)


def with_docs(facts: CaseFacts, *docs: DocumentFacts) -> CaseFacts:
    all_docs = (*facts.documents, *docs)
    return replace(facts, documents=all_docs, kinds_present=frozenset(x.kind for x in all_docs))
