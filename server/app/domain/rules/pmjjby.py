"""PMJJBY: life cover for death from any cause, with a lien period for new enrolments."""

from app.domain.config.loader import RulesConfig
from app.domain.facts import CaseFacts
from app.domain.models import CaseMode, CoverStatus, EventType, FlagSeverity, Scheme
from app.domain.results import Alert, Cover, Deadline, Flag, Reason, SchemeResult
from app.domain.rules.common import (
    deadline,
    evidence,
    over_age,
    premium_status,
    protect_alert,
    single_reason,
)

SCHEME = Scheme.PMJJBY


def evaluate(facts: CaseFacts, config: RulesConfig) -> SchemeResult:
    cfg = config.pmjjby
    status = premium_status(facts, cfg, config)

    if status.last_debit is None:
        return single_reason(SCHEME, CoverStatus.NOT_FOUND, Reason("no_premium_found"))

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

    if facts.mode is CaseMode.PROTECT:
        return SchemeResult(
            cover=Cover(
                SCHEME,
                CoverStatus.ELIGIBLE,
                cfg.sum_assured,
                proof,
                (Reason("premium_debited_current_year"),),
            ),
            alerts=(Alert("alert.cover_active", SCHEME),),
        )

    if facts.event_type is EventType.ACCIDENTAL_DISABILITY:
        return single_reason(SCHEME, CoverStatus.INELIGIBLE, Reason("life_cover_death_only"), proof)

    if (
        facts.event_type is EventType.NATURAL_DEATH
        and facts.event_date is not None
        and status.enrolled_on is not None
        and (facts.event_date - status.enrolled_on).days < cfg.lien_days
    ):
        params = {
            "days_since_enrolment": (facts.event_date - status.enrolled_on).days,
            "lien_days": cfg.lien_days,
        }
        return SchemeResult(
            cover=Cover(
                SCHEME,
                CoverStatus.INELIGIBLE,
                0,
                proof,
                (Reason("death_within_lien_period", params),),
            ),
            flags=(Flag("death_within_lien_period", FlagSeverity.INFO, params),),
        )

    reasons = [Reason("premium_debited_current_year")]
    cover_status = CoverStatus.ELIGIBLE
    if facts.event_type is None:
        cover_status = CoverStatus.LIKELY_ELIGIBLE
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
        cover=Cover(SCHEME, cover_status, cfg.sum_assured, proof, tuple(reasons)),
        deadlines=deadlines,
    )
