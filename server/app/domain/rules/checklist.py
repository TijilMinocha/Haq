from collections.abc import Iterable

from app.domain.config.loader import RulesConfig
from app.domain.facts import CaseFacts
from app.domain.models import ELIGIBLE_LIKE, CaseMode, FlagSeverity, Scheme
from app.domain.results import ChecklistItem, Cover, Flag

# Only these schemes pay on accident and therefore need police and medical papers.
_ACCIDENT_SCHEMES = frozenset({Scheme.PMSBY, Scheme.RUPAY_PMJDY})


def build(facts: CaseFacts, covers: Iterable[Cover], config: RulesConfig) -> list[ChecklistItem]:
    if facts.mode is not CaseMode.CLAIM or facts.event_type is None:
        return []
    items = []
    for cover in covers:
        if cover.status not in ELIGIBLE_LIKE:
            continue
        for kind in config.documents_for(cover.scheme).get(facts.event_type, ()):
            items.append(
                ChecklistItem(
                    scheme=cover.scheme,
                    document_kind=kind,
                    required=True,
                    received=kind in facts.kinds_present,
                )
            )
    return items


def accident_document_flags(
    facts: CaseFacts, covers: Iterable[Cover], config: RulesConfig
) -> list[Flag]:
    if facts.mode is not CaseMode.CLAIM or facts.event_type is None:
        return []
    needs_accident_docs = any(
        c.scheme in _ACCIDENT_SCHEMES and c.status in ELIGIBLE_LIKE for c in covers
    )
    required = config.accident_documents.get(facts.event_type, ())
    missing = [k.value for k in required if k not in facts.kinds_present]
    if not needs_accident_docs or not missing:
        return []
    return [Flag("accident_docs_missing", FlagSeverity.BLOCKER, {"missing": missing})]
