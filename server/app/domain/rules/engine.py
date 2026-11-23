"""Runs every scheme module and the cross-document checks, then merges the results.

Adding a scheme means adding a module to SCHEME_MODULES and its block to the FY YAML.
"""

from collections.abc import Callable

from app.domain.config.loader import RulesConfig
from app.domain.facts import CaseFacts
from app.domain.models import ELIGIBLE_LIKE, CaseMode, FlagSeverity
from app.domain.results import EvaluationResult, Flag, SchemeResult
from app.domain.rules import alerts, checklist, crosscheck, deadlines, pmjjby, pmsby, rupay

SchemeModule = Callable[[CaseFacts, RulesConfig], SchemeResult]
SCHEME_MODULES: tuple[SchemeModule, ...] = (pmjjby.evaluate, pmsby.evaluate, rupay.evaluate)

_SEVERITY_ORDER = {FlagSeverity.BLOCKER: 0, FlagSeverity.WARNING: 1, FlagSeverity.INFO: 2}


def _dedupe(flags: list[Flag]) -> list[Flag]:
    seen: set[str] = set()
    unique = []
    for flag in flags:
        key = f"{flag.code}|{sorted(flag.params.items())!r}"
        if key not in seen:
            seen.add(key)
            unique.append(flag)
    return unique


def evaluate(facts: CaseFacts, config: RulesConfig) -> EvaluationResult:
    results = [module(facts, config) for module in SCHEME_MODULES]
    covers = tuple(r.cover for r in results)
    all_deadlines = tuple(d for r in results for d in r.deadlines)

    flags = _dedupe(
        [
            *(f for r in results for f in r.flags),
            *crosscheck.evaluate(facts, config),
            *checklist.accident_document_flags(facts, covers, config),
            *deadlines.window_flags(all_deadlines, config),
        ]
    )
    flags.sort(key=lambda f: _SEVERITY_ORDER[f.severity])

    total = 0
    if facts.mode is CaseMode.CLAIM:
        total = sum(c.amount for c in covers if c.status in ELIGIBLE_LIKE)

    return EvaluationResult(
        total_claimable=total,
        covers=covers,
        flags=tuple(flags),
        checklist=tuple(checklist.build(facts, covers, config)),
        deadlines=tuple(sorted(all_deadlines, key=lambda d: d.due_date)),
        alerts=tuple(alerts.protect_alerts(facts, (a for r in results for a in r.alerts))),
    )
