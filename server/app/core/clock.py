"""The one place that answers which day it is in India, whatever the server's clock says."""

from datetime import date, datetime, timedelta, timezone

# A fixed offset rather than zoneinfo: India has no daylight saving, and zoneinfo needs the
# extra tzdata package to work on Windows.
IST = timezone(timedelta(hours=5, minutes=30))


def today_ist() -> date:
    return datetime.now(IST).date()
