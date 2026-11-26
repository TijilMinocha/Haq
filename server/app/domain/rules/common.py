from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.config.loader import PremiumScheme, RulesConfig
from app.domain.facts import CaseFacts, Txn
from app.domain.models import CaseMode, CoverStatus, Scheme
from app.domain.passbook import cover_year_of, premiums, year_paid_by
from app.domain.results import Alert, Cover, Deadline, Evidence, Params, Reason, SchemeResult


@dataclass(frozen=True)
class PremiumStatus:
    debits: tuple[Txn, ...]
    covering: Txn | None
    """The debit that paid for the cover year containing the reference date."""
    enrolled_on: date | None
    """Set when no debit paid for the year before, so `covering` was the first premium."""

    @property
    def last_debit(self) -> Txn | None:
        return self.debits[-1] if self.debits else None


def premium_status(facts: CaseFacts, scheme: PremiumScheme, config: RulesConfig) -> PremiumStatus:
    start = config.cover_year_start
    debits = premiums(facts.transactions, scheme)
    target = cover_year_of(facts.reference_date, start)
    paid_years = {year_paid_by(t.date, scheme, start) for t in debits}
    # The latest debit that had paid for the target year by the reference date. Picking the
    # latest debit per year instead let a second debit later in the year erase cover that the
    # renewal had already bought, and lapse a policy that was in force when the event happened.
    covering = next(
        (
            t
            for t in reversed(debits)
            if t.date <= facts.reference_date and year_paid_by(t.date, scheme, start) == target
        ),
        None,
    )
    enrolled_on = covering.date if covering and (target - 1) not in paid_years else None
    return PremiumStatus(tuple(debits), covering, enrolled_on)


def age_on(dob: date, day: date) -> int:
    return day.year - dob.year - ((day.month, day.day) < (dob.month, dob.day))


def over_age(facts: CaseFacts, max_age: int) -> bool:
    return (
        facts.subject_dob is not None and age_on(facts.subject_dob, facts.reference_date) >= max_age
    )


def evidence(txn: Txn) -> Evidence:
    return Evidence(date=txn.date, narration=txn.narration, amount=txn.amount)


def deadline(
    scheme: Scheme, code: str, start: date, within_days: int, today: date, *, hard: bool
) -> Deadline:
    due = start + timedelta(days=within_days)
    return Deadline(scheme=scheme, code=code, due_date=due, days_left=(due - today).days, hard=hard)


def single_reason(
    scheme: Scheme,
    status: CoverStatus,
    reason: Reason,
    proof: tuple[Evidence, ...] = (),
    amount: int = 0,
) -> SchemeResult:
    return SchemeResult(cover=Cover(scheme, status, amount, proof, (reason,)))


def protect_alert(
    facts: CaseFacts, code: str, scheme: Scheme, params: Params | None = None
) -> tuple[Alert, ...]:
    if facts.mode is not CaseMode.PROTECT:
        return ()
    return (Alert(code, scheme, params or {}),)
