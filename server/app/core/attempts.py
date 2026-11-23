import time
from dataclasses import dataclass, field

from app.core.errors import too_many_attempts


@dataclass
class AttemptLimiter:
    """Locks a key (case code or email) after repeated failures.

    In-process only; a multi-instance deploy would move this to Postgres.
    """

    max_attempts: int
    lock_seconds: int
    _failures: dict[str, list[float]] = field(default_factory=dict)

    def check(self, key: str) -> None:
        recent = self._recent(key)
        if len(recent) >= self.max_attempts:
            raise too_many_attempts(self.lock_seconds // 60)

    def fail(self, key: str) -> None:
        self._failures[key] = [*self._recent(key), time.monotonic()]

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def _recent(self, key: str) -> list[float]:
        cutoff = time.monotonic() - self.lock_seconds
        return [t for t in self._failures.get(key, []) if t > cutoff]
