"""PMSBY: accident cover for death or disability. Natural death is not covered."""

from app.domain.config.loader import RulesConfig
from app.domain.facts import CaseFacts
from app.domain.models import CaseMode, CoverStatus, EventType, Scheme
from app.domain.results import Alert, Cover, Deadline, Reason, SchemeResult
from app.domain.rules.common import (
    deadline,
    evidence,
    over_age,
    premium_status,
    protect_alert,
    single_reason,
)

SCHEME = Scheme.PMSBY


def evaluate(facts: CaseFacts, config: RulesConfig) -> SchemeResult:
    cfg = config.pmsby
    status = premium_status(facts, cfg, config)

    if status.last_debit is None:
        return single_reason(SCHEME, CoverStatus.NOT_FOUND, Reason("no_premium_found"))

    if facts.mode is CaseMode.CLAIM and facts.event_type is EventType.NATURAL_DEATH:
        return single_reason(SCHEME, CoverStatus.INELIGIBLE, Reason("accident_only_cover"))

    if status.covering is None:
        last = status.last_debit.date.isoformat()
        return SchemeResult(
            cover=Cover(
                SCHEME,
                CoverStatus.LAPSED,
                0,
                (evidence(status.last_debit),),
                (Reason("no_premium_this_cover_year", {"last_debit": last}),),
            ),
            alerts=protect_alert(facts, "alert.cover_lapsed", SCHEME, {"last_debit": last}),
        )

    proof = (evidence(status.covering),)
    if over_age(facts, cfg.max_cover_age):
        reason = Reason("age_above_limit", {"max_age": cfg.max_cover_age})
        return single_reason(SCHEME, CoverStatus.INELIGIBLE, reason, proof)

    full = cfg.death_or_total_disability
    if facts.mode is CaseMode.PROTECT:
        return SchemeResult(
            cover=Cover(
                SCHEME, CoverStatus.ELIGIBLE, full, proof, (Reason("premium_debited_current_year"),)
            ),
            alerts=(Alert("alert.cover_active", SCHEME),),
        )

    reasons = [Reason("premium_debited_current_year")]
    match facts.event_type:
        case EventType.ACCIDENTAL_DEATH:
            cover_status = CoverStatus.ELIGIBLE
            reasons.append(Reason("accidental_event"))
        case EventType.ACCIDENTAL_DISABILITY:
            # The payout depends on total vs partial disability, which only the certificate shows.
            cover_status = CoverStatus.NEEDS_VERIFICATION
            reasons.append(
                Reason(
                    "disability_extent_needed", {"total": full, "partial": cfg.partial_disability}
                )
            )
        case _:
            cover_status = CoverStatus.NEEDS_VERIFICATION
            reasons.append(Reason("event_details_missing"))

    deadlines: tuple[Deadline, ...] = ()
    if facts.event_date is not None:
        deadlines = (
            deadline(
                SCHEME,
                "claim_submission",
                facts.event_date,
                cfg.claim_preferred_within_days,
                facts.today,
                hard=False,
            ),
        )
    return SchemeResult(
        cover=Cover(SCHEME, cover_status, full, proof, tuple(reasons)), deadlines=deadlines
    )
