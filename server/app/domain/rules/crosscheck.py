"""Checks that span documents: names, dates of birth, accounts, nominee and OCR quality."""

from app.domain.config.loader import RulesConfig
from app.domain.facts import CaseFacts, DocumentFacts
from app.domain.matching import compare_names
from app.domain.models import CaseMode, DocumentKind, FlagSeverity
from app.domain.results import Flag

# Documents that name the insured person. The passbook is the bank's record, so it is the
# reference the others must match.
_IDENTITY_KINDS = (
    DocumentKind.PASSBOOK,
    DocumentKind.DEATH_CERTIFICATE,
    DocumentKind.AADHAAR_DECEASED,
    DocumentKind.POSTMORTEM,
    DocumentKind.DISABILITY_CERTIFICATE,
)


def _identity_docs(facts: CaseFacts) -> list[DocumentFacts]:
    order = {kind: i for i, kind in enumerate(_IDENTITY_KINDS)}
    docs = [d for d in facts.documents if d.kind in order]
    return sorted(docs, key=lambda d: order[d.kind])


def name_flags(facts: CaseFacts, config: RulesConfig) -> list[Flag]:
    named = [(d.kind, d.name) for d in _identity_docs(facts) if d.name]
    if len(named) < 2:
        return []
    (ref_kind, ref_name), flags = named[0], []
    for kind, name in named[1:]:
        if not compare_names(ref_name, name, config.name_threshold).same:
            flags.append(
                Flag(
                    "name_mismatch",
                    FlagSeverity.BLOCKER,
                    {"documents": [ref_kind.value, kind.value], "values": [ref_name, name]},
                )
            )
    return flags


def dob_flags(facts: CaseFacts) -> list[Flag]:
    dated = [d for d in _identity_docs(facts) if d.date_of_birth]
    if len(dated) < 2:
        return []
    reference = dated[0]
    return [
        Flag(
            "dob_mismatch",
            FlagSeverity.WARNING,
            {
                "documents": [reference.kind.value, other.kind.value],
                "values": [str(reference.date_of_birth), str(other.date_of_birth)],
            },
        )
        for other in dated[1:]
        if other.date_of_birth != reference.date_of_birth
    ]


def account_flags(facts: CaseFacts) -> list[Flag]:
    accounts = sorted({p.account_last4 for p in facts.passbooks if p.account_last4})
    if len(accounts) < 2:
        return []
    return [Flag("account_mismatch", FlagSeverity.BLOCKER, {"accounts": accounts})]


def has_nominee(facts: CaseFacts) -> bool:
    return bool(facts.nominee_name) or any(p.nominee_name for p in facts.passbooks)


def nominee_flags(facts: CaseFacts) -> list[Flag]:
    # Without a passbook we cannot know whether a nominee is registered.
    if facts.mode is not CaseMode.CLAIM or not facts.passbooks or has_nominee(facts):
        return []
    return [Flag("nominee_missing", FlagSeverity.BLOCKER)]


def confidence_flags(facts: CaseFacts, config: RulesConfig) -> list[Flag]:
    return [
        Flag(
            "ocr_low_confidence",
            FlagSeverity.WARNING,
            {"document_id": d.document_id, "document": d.kind.value},
        )
        for d in facts.documents
        if not d.corrected and d.confidence < config.min_confidence
    ]


def evaluate(facts: CaseFacts, config: RulesConfig) -> list[Flag]:
    return [
        *name_flags(facts, config),
        *dob_flags(facts),
        *account_flags(facts),
        *nominee_flags(facts),
        *confidence_flags(facts, config),
    ]
