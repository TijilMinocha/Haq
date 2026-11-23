import re
import time
from collections import deque
from dataclasses import dataclass, field

_WINDOW_SECONDS = 60.0
_PRUNE_EVERY = 500


@dataclass(frozen=True)
class Rule:
    name: str
    method: str
    path: re.Pattern[str]
    per_minute: int


@dataclass
class SlidingWindowLimiter:
    """Counts requests per (rule, client) over the last minute.

    In-process: fine for the single free instance. Several instances would each allow the
    full rate, which still caps abuse well enough for this deployment.
    """

    rules: tuple[Rule, ...]
    _hits: dict[tuple[str, str], deque[float]] = field(default_factory=dict)
    _calls: int = 0

    def match(self, method: str, path: str) -> Rule | None:
        return next((r for r in self.rules if r.method == method and r.path.fullmatch(path)), None)

    def hit(self, rule: Rule, client: str) -> float | None:
        """Records a request; returns seconds to wait if it is over the limit."""
        now = time.monotonic()
        self._calls += 1
        if self._calls % _PRUNE_EVERY == 0:
            self._prune(now)
        hits = self._hits.setdefault((rule.name, client), deque())
        while hits and now - hits[0] > _WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= rule.per_minute:
            return _WINDOW_SECONDS - (now - hits[0])
        hits.append(now)
        return None

    def _prune(self, now: float) -> None:
        stale = [k for k, v in self._hits.items() if not v or now - v[-1] > _WINDOW_SECONDS]
        for key in stale:
            del self._hits[key]


def default_rules(uploads_per_minute: int, auth_per_minute: int) -> tuple[Rule, ...]:
    return (
        Rule("upload", "POST", re.compile(r"/api/v1/cases/[^/]+/documents"), uploads_per_minute),
        Rule(
            "auth",
            "POST",
            re.compile(r"/api/v1/(auth/login|cases|cases/resume|demo/scenarios/[^/]+)"),
            auth_per_minute,
        ),
    )
