from collections.abc import Iterable

from app.domain.facts import CaseFacts
from app.domain.models import CaseMode
from app.domain.results import Alert
from app.domain.rules.crosscheck import has_nominee


def protect_alerts(facts: CaseFacts, scheme_alerts: Iterable[Alert]) -> list[Alert]:
    if facts.mode is not CaseMode.PROTECT:
        return []
    alerts = list(scheme_alerts)
    if facts.passbooks and not has_nominee(facts):
        alerts.append(Alert("alert.nominee_missing"))
    # Problems first, reassurance last, so the one action the user must take is on top.
    return sorted(alerts, key=lambda a: a.code == "alert.cover_active")
