import logging
import math
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.errors import error_body
from app.core.rate_limit import SlidingWindowLimiter, default_rules
from app.core.request_context import request_id

log = logging.getLogger("haq.access")

_INCOMING_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
# Room for the multipart envelope around the file itself.
_MULTIPART_OVERHEAD_BYTES = 256 * 1024
# A digit string longer than this is past any upload limit, and int() on it is slow.
_LONGEST_LENGTH_BYTES = 12
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000",
    # Case data is personal; no browser or proxy should keep a copy.
    "Cache-Control": "no-store",
}

Next = Callable[[Request], Awaitable[Response]]


def client_host(request: Request) -> str:
    # Uvicorn runs with --proxy-headers on Render, so this is the caller, not the proxy.
    return request.client.host if request.client else "unknown"


def _too_large(length: str | None, max_body: int) -> bool:
    if length is None or not length.isdigit():
        return False
    return len(length) > _LONGEST_LENGTH_BYTES or int(length) > max_body


def install_middleware(app: FastAPI, settings: Settings) -> None:
    max_body = settings.max_upload_mb * 1024 * 1024 + _MULTIPART_OVERHEAD_BYTES
    limiter = SlidingWindowLimiter(
        default_rules(settings.rate_limit_uploads, settings.rate_limit_auth)
    )

    @app.middleware("http")
    async def guard(request: Request, call_next: Next) -> Response:
        length = request.headers.get("content-length")
        if _too_large(length, max_body):
            return JSONResponse(
                error_body(
                    "file_too_large", "File is too large.", {"max_mb": settings.max_upload_mb}
                ),
                status_code=413,
            )
        rule = (
            limiter.match(request.method, request.url.path)
            if settings.rate_limits_enabled
            else None
        )
        if rule is not None:
            wait = limiter.hit(rule, client_host(request))
            if wait is not None:
                log.warning("rate limited", extra={"rule": rule.name})
                return JSONResponse(
                    error_body(
                        "too_many_attempts",
                        "Too many requests. Please wait a minute.",
                        {"minutes": 1, "retry_after_seconds": math.ceil(wait)},
                    ),
                    status_code=429,
                    headers={"Retry-After": str(math.ceil(wait))},
                )
        return await call_next(request)

    # Registered last so it runs first: every response, even a rejection above, gets an id.
    @app.middleware("http")
    async def context(request: Request, call_next: Next) -> Response:
        incoming = request.headers.get("x-request-id", "")
        # fullmatch, because $ also matches before a trailing newline and that would let a
        # caller inject a header or a log line break through the echoed id.
        rid = incoming if _INCOMING_ID.fullmatch(incoming) else uuid.uuid4().hex
        token = request_id.set(rid)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Handled here rather than by Starlette's outer error middleware, so the 500 still
            # passes through CORS and the client can show the request id.
            log.exception("unhandled error")
            response = JSONResponse(
                error_body(
                    "internal_error", "Something went wrong. Please try again.", {"request_id": rid}
                ),
                status_code=500,
            )
        finally:
            request_id.reset(token)
        response.headers["X-Request-ID"] = rid
        for name, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        # Paths carry opaque ids only; query strings and bodies are never logged.
        log.info(
            "request",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000),
            },
        )
        return response
