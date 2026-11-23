"""Logging setup. In production every line is one JSON object, so Render's log search can
filter by request_id; locally it stays human-readable."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.request_context import request_id

# Attributes every LogRecord has; anything else was passed with `extra=` and is logged.
_STANDARD = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id.get() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        entry.update({k: v for k, v in vars(record).items() if k not in _STANDARD})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure_logging(level: str, as_json: bool) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())
    handler.setFormatter(
        JsonFormatter()
        if as_json
        else logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # Our own access log replaces uvicorn's, which lacks request ids and timings.
    logging.getLogger("uvicorn.access").disabled = True
