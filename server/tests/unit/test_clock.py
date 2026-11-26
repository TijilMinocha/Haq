from datetime import UTC, date, datetime, tzinfo

import pytest

from app.core import clock


@pytest.mark.parametrize(
    ("now_utc", "expected"),
    [
        (datetime(2026, 1, 1, 18, 29, tzinfo=UTC), date(2026, 1, 1)),
        (datetime(2026, 1, 1, 18, 30, tzinfo=UTC), date(2026, 1, 2)),
        (datetime(2026, 1, 1, 20, 0, tzinfo=UTC), date(2026, 1, 2)),
    ],
)
def test_today_ist_rolls_over_at_indian_midnight(
    monkeypatch: pytest.MonkeyPatch, now_utc: datetime, expected: date
) -> None:
    fixed_now = now_utc

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            return fixed_now.astimezone(tz) if tz else fixed_now

    monkeypatch.setattr(clock, "datetime", _FrozenDatetime)
    assert clock.today_ist() == expected
