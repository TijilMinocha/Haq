from collections.abc import Iterable

from app.domain.config.loader import RulesConfig
from app.domain.models import FlagSeverity
from app.domain.results import Deadline, Flag


def window_flags(deadlines: Iterable[Deadline], config: RulesConfig) -> list[Flag]:
    flags = []
    for d in deadlines:
        params = {"scheme": d.scheme.value, "deadline": d.code, "due_date": d.due_date.isoformat()}
        if d.days_left < 0:
            flags.append(
                Flag(
                    "claim_window_passed",
                    FlagSeverity.WARNING,
                    {**params, "days_late": -d.days_left},
                )
            )
        elif d.days_left <= config.closing_warning_days:
            flags.append(
                Flag(
                    "claim_window_closing",
                    FlagSeverity.WARNING,
                    {**params, "days_left": d.days_left},
                )
            )
    return flags
