import time
from dataclasses import dataclass, field
from typing import Protocol

from app.core.errors import too_many_attempts


class AttemptStore(Protocol):
    """Locks a key (case code or email) after repeated failed attempts."""

    async def check(self, key: str) -> None: ...
    async def fail(self, key: str) -> None: ...
    async def reset(self, key: str) -> None: ...


@dataclass
class InMemoryAttemptStore:
    max_attempts: int
    lock_seconds: int
    _failures: dict[str, list[float]] = field(default_factory=dict)

    async def check(self, key: str) -> None:
        if len(self._recent(key)) >= self.max_attempts:
            raise too_many_attempts(self.lock_seconds // 60)

    async def fail(self, key: str) -> None:
        self._failures[key] = [*self._recent(key), time.monotonic()]

    async def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def _recent(self, key: str) -> list[float]:
        cutoff = time.monotonic() - self.lock_seconds
        return [t for t in self._failures.get(key, []) if t > cutoff]
