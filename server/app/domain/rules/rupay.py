"""RuPay PMJDY: free accident cover that is void unless the card was used in the 90 days before.

Only card-channel transactions count. UPI and AEPS do not prove the card was used, so they
lead to verification by the bank rather than a pass.
"""

from datetime import date, timedelta

from app.domain.config.loader import RulesConfig, RupayConfig
from app.domain.facts import CaseFacts, Passbook, Txn
from app.domain.models import CaseMode, CoverStatus, EventType, FlagSeverity, Scheme
from app.domain.passbook import card_txns_between
from app.domain.results import Alert, Cover, Flag, Reason, SchemeResult
from app.domain.rules.common import deadline, evidence, protect_alert, single_reason

SCHEME = Scheme.RUPAY_PMJDY
_EARLIEST = date.min


def card_amount(passbook: Passbook | None, cfg: RupayConfig) -> tuple[int, Reason]:
    issued = passbook.card_issued_on if passbook else None
    if issued is None:
        return cfg.old_card_amount, Reason("card_issue_date_unknown")
    if issued > cfg.new_card_after:
        return cfg.new_card_amount, Reason("new_card_amount")
    return cfg.old_card_amount, Reason("old_card_amount")


def evaluate(facts: CaseFacts, config: RulesConfig) -> SchemeResult:
    cfg = config.rupay
    passbook = facts.passbook
    card_bin = passbook.card_bin if passbook else None
    ever_used = card_txns_between(
        facts.transactions, _EARLIEST, facts.today, cfg.counting_channels, config
    )

    if card_bin is None and not ever_used:
        return single_reason(SCHEME, CoverStatus.NOT_FOUND, Reason("no_rupay_card"))
    if card_bin is not None and card_bin not in cfg.eligible_bins:
        return single_reason(
            SCHEME, CoverStatus.INELIGIBLE, Reason("card_not_eligible", {"card_bin": card_bin})
        )

    amount, amount_reason = card_amount(passbook, cfg)
    if facts.mode is CaseMode.PROTECT:
        return _protect(facts, cfg, amount, amount_reason, ever_used[-1] if ever_used else None)
    return _claim(facts, config, amount, amount_reason)


def _protect(
    facts: CaseFacts, cfg: RupayConfig, amount: int, amount_reason: Reason, last_use: Txn | None
) -> SchemeResult:
    if last_use is None:
        return SchemeResult(
            cover=Cover(SCHEME, CoverStatus.LAPSED, 0, (), (Reason("no_card_txn_in_window"),)),
            alerts=protect_alert(facts, "alert.cover_lapsed", SCHEME),
        )
    expires = last_use.date + timedelta(days=cfg.txn_lookback_days)
    days_left = (expires - facts.today).days
    if days_left < 0:
        params = {"last_card_use": last_use.date.isoformat()}
        return SchemeResult(
            cover=Cover(
                SCHEME, CoverStatus.LAPSED, 0, (), (Reason("no_card_txn_in_window", params),)
            ),
            alerts=(Alert("alert.cover_lapsed", SCHEME, params),),
        )
    window = {"expires_on": expires.isoformat(), "days_left": days_left}
    alert = (
        Alert("alert.rupay_expiring", SCHEME, window)
        if days_left <= cfg.expiry_warning_days
        else Alert("alert.cover_active", SCHEME)
    )
    return SchemeResult(
        cover=Cover(
            SCHEME,
            CoverStatus.ELIGIBLE,
            amount,
            (evidence(last_use),),
            (Reason("card_txn_within_lookback", window), amount_reason),
        ),
        alerts=(alert,),
    )


def _claim(
    facts: CaseFacts, config: RulesConfig, amount: int, amount_reason: Reason
) -> SchemeResult:
    cfg = config.rupay
    if facts.event_type is EventType.NATURAL_DEATH:
        return single_reason(SCHEME, CoverStatus.INELIGIBLE, Reason("accident_only_cover"))
    if facts.event_type is None or facts.event_date is None:
        return single_reason(
            SCHEME, CoverStatus.NEEDS_VERIFICATION, Reason("event_details_missing"), amount=amount
        )

    event = facts.event_date
    since = event - timedelta(days=cfg.txn_lookback_days)
    counted = card_txns_between(facts.transactions, since, event, cfg.counting_channels, config)
    intimation = (
        deadline(
            SCHEME, "claim_intimation", event, cfg.intimation_within_days, facts.today, hard=True
        ),
    )

    if counted:
        last = counted[-1]
        reason = Reason("card_txn_within_lookback", {"days_before_event": (event - last.date).days})
        # The bank still confirms the card was active, so this is never a plain "eligible".
        return SchemeResult(
            cover=Cover(
                SCHEME,
                CoverStatus.LIKELY_ELIGIBLE,
                amount,
                (evidence(last),),
                (reason, amount_reason),
            ),
            deadlines=intimation,
        )

    unverifiable = card_txns_between(
        facts.transactions, since, event, cfg.unverifiable_channels, config
    )
    if unverifiable:
        params = {"lookback_days": cfg.txn_lookback_days}
        return SchemeResult(
            cover=Cover(
                SCHEME,
                CoverStatus.NEEDS_VERIFICATION,
                amount,
                tuple(evidence(t) for t in unverifiable[-3:]),
                (Reason("only_unverifiable_txns", params), amount_reason),
            ),
            flags=(Flag("rupay_txn_unverifiable", FlagSeverity.WARNING, params),),
            deadlines=intimation,
        )

    params = {"lookback_days": cfg.txn_lookback_days}
    return SchemeResult(
        cover=Cover(
            SCHEME, CoverStatus.INELIGIBLE, 0, (), (Reason("no_card_txn_in_window", params),)
        ),
        flags=(Flag("rupay_no_recent_txn", FlagSeverity.INFO, params),),
    )
