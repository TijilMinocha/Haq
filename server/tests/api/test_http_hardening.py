"""Audit items 12-16: logs, CORS, security headers, rate limits and request ids."""

import logging
from typing import Any

import pytest
from httpx import AsyncClient

from .conftest import ORIGIN, add_document, app_client, create_case, login

_SECURITY_HEADERS = (
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "strict-transport-security",
    "cache-control",
)


def _secrets(created: dict[str, str]) -> tuple[str, ...]:
    # The case id is not a secret on its own: reading the case also needs the token.
    return (created["access_token"],)


async def test_an_incoming_request_id_cannot_break_the_response() -> None:
    async with app_client() as (_, client):
        echoed = await client.get("/health", headers={"X-Request-ID": "phone-42"})
        injected = await client.get("/health", headers={"X-Request-ID": "phone-42\n"})
        long = await client.get("/health", headers={"X-Request-ID": "a" * 65})
    assert echoed.headers["x-request-id"] == "phone-42"
    # A trailing newline passes a "$" anchored pattern but not a full match.
    assert injected.headers["x-request-id"] != "phone-42\n"
    assert len(injected.headers["x-request-id"]) == 32
    assert len(long.headers["x-request-id"]) == 32


async def test_only_configured_origins_are_allowed() -> None:
    async with app_client() as (_, client):
        mine = await client.get("/health", headers={"Origin": ORIGIN})
        theirs = await client.get("/health", headers={"Origin": "https://evil.example"})
        preflight = await client.options(
            "/cases",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert mine.headers["access-control-allow-origin"] == ORIGIN
    assert "access-control-allow-origin" not in theirs.headers
    assert "access-control-allow-origin" not in preflight.headers
    # No credentials are allowed, so a wildcard could never become a session-bearing call.
    assert "access-control-allow-credentials" not in mine.headers


async def test_security_headers_are_on_every_response() -> None:
    async with app_client() as (_, client):
        created = await create_case(client)
        headers = {"X-Case-Token": created["access_token"]}
        responses = [
            await client.get("/health"),
            await client.get(f"/cases/{created['case_id']}"),
            await client.get(f"/cases/{created['case_id']}", headers=headers),
            await client.get(f"/cases/{created['case_id']}", headers={"X-Case-Token": "wrong"}),
            await client.get("/cases/c_missing", headers=headers),
            await client.get("/nowhere"),
            await client.post(
                f"/cases/{created['case_id']}/documents",
                headers=headers,
                data={"kind": "fir"},
                files={"file": ("x.txt", b"hello", "text/plain")},
            ),
            await client.patch(
                f"/cases/{created['case_id']}", headers=headers, json={"subject": {"name": 1}}
            ),
        ]
        statuses = [r.status_code for r in responses]
        checks = [
            (r.status_code, {h: r.headers.get(h) for h in _SECURITY_HEADERS}) for r in responses
        ]

    assert statuses == [200, 401, 200, 401, 404, 404, 415, 422]
    for status, present in checks:
        assert all(present.values()), f"missing security header on {status}: {present}"
        assert present["cache-control"] == "no-store"


async def test_refusals_from_the_middleware_carry_headers_too() -> None:
    async with app_client(env="dev", max_upload_mb=1, rate_limit_auth=1) as (_, client):
        created = await create_case(client)
        headers = {"X-Case-Token": created["access_token"]}
        too_large = await client.post(
            f"/cases/{created['case_id']}/documents",
            headers={**headers, "Content-Length": str(3 * 1024 * 1024)},
            content=b"x",
        )
        limited = await client.post("/cases", json={"mode": "claim", "pin": "1234"})
    assert (too_large.status_code, too_large.json()["error"]["code"]) == (413, "file_too_large")
    assert (limited.status_code, limited.json()["error"]["code"]) == (429, "too_many_attempts")
    for response in (too_large, limited):
        for name in _SECURITY_HEADERS:
            assert response.headers.get(name)


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        ("login", 429),
        ("resume", 429),
        ("create", 429),
        ("upload", 429),
    ],
)
async def test_the_costly_routes_are_rate_limited(call: str, expected: int) -> None:
    async with app_client(env="dev", rate_limit_auth=1, rate_limit_uploads=1) as (_, client):
        if call == "upload":
            created = await create_case(client)
            await add_document(
                client, created["case_id"], {"X-Case-Token": created["access_token"]}
            )
            response = await client.post(
                f"/cases/{created['case_id']}/documents",
                headers={"X-Case-Token": created["access_token"]},
                data={"kind": "fir"},
                files={"file": ("fir.jpg", b"\xff\xd8photo", "image/jpeg")},
            )
        elif call == "login":
            await login(client)
            response = await client.post(
                "/auth/login", json={"email": "mitra@haq.demo", "password": "haq-demo-2026"}
            )
        elif call == "resume":
            created = await create_case(client, pin="4321")
            await client.post(
                "/cases/resume", json={"case_code": created["case_code"], "pin": "0000"}
            )
            response = await client.post(
                "/cases/resume", json={"case_code": created["case_code"], "pin": "4321"}
            )
        else:
            await create_case(client)
            response = await client.post("/cases", json={"mode": "claim", "pin": "1234"})
    assert response.status_code == expected
    assert response.json()["error"]["code"] == "too_many_attempts"
    assert int(response.headers["retry-after"]) >= 1


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        extra = {k: v for k, v in vars(record).items() if k not in {"msg", "args", "message"}}
        self.lines.append(f"{record.getMessage()} {extra}")


async def test_logs_carry_no_tokens_pins_or_personal_data() -> None:
    async with app_client() as (_, client):
        # Attached after the app is built, because create_app replaces the root handlers.
        capture = _Capture()
        logging.getLogger().addHandler(capture)
        try:
            created = await create_case(client, pin="4681")
            headers = {"X-Case-Token": created["access_token"]}
            document_id = await add_document(client, created["case_id"], headers)
            await client.patch(
                f"/cases/{created['case_id']}/documents/{document_id}",
                headers=headers,
                json={"fields": {"notes": "aadhaar 1234 5678 9012"}},
            )
            login_res = await client.post(
                "/auth/login", json={"email": "mitra@haq.demo", "password": "haq-demo-2026"}
            )
            operator_token: str = login_res.json()["access_token"]
            await client.get("/auth/me", headers={"Authorization": f"Bearer {operator_token}"})
            await client.post(
                "/cases/resume", json={"case_code": created["case_code"], "pin": "4681"}
            )
            await client.get(f"/cases/{created['case_id']}", headers={"X-Case-Token": "wrong"})
        finally:
            logging.getLogger().removeHandler(capture)

    written = "\n".join(capture.lines)
    assert written, "no log lines were captured"
    for secret in (
        "4681",
        "haq-demo-2026",
        "1234 5678 9012",
        "wrong",
        operator_token,
        *_secrets(created),
    ):
        assert secret not in written
    assert "authorization" not in written.lower()
    # The access log still says what happened, which is what makes it useful.
    assert "request" in written and "/api/v1/cases/" in written


async def test_the_access_log_never_contains_the_query_string() -> None:
    # Only the server's own logger: httpx logs the test client's URLs verbatim.
    access_log = logging.getLogger("haq.access")
    async with app_client() as (_, client):
        capture = _Capture()
        access_log.addHandler(capture)
        try:
            await client.get("/meta/schemes?token=leak-me&pin=9876")
        finally:
            access_log.removeHandler(capture)
    written = "\n".join(capture.lines)
    assert "/meta/schemes" in written
    assert "leak-me" not in written and "9876" not in written


async def test_a_garbage_request_id_still_gives_every_response_an_id() -> None:
    async with app_client(env="dev", rate_limit_auth=0) as (_, client):
        responses: list[Any] = [
            await client.get("/health", headers={"X-Request-ID": "  "}),
            await client.get("/nowhere"),
        ]
    for response in responses:
        assert len(response.headers["x-request-id"]) == 32


async def test_cors_headers_are_added_to_an_error_from_the_middleware() -> None:
    async with app_client(max_upload_mb=1) as (_, client):
        res = await client.post(
            "/cases/c_x/documents",
            headers={"Content-Length": str(3 * 1024 * 1024), "Origin": ORIGIN},
            content=b"x",
        )
    assert res.status_code == 413
    assert res.headers["access-control-allow-origin"] == ORIGIN


async def test_a_wildcard_origin_is_refused_by_settings(client: AsyncClient) -> None:
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(env="test", cors_origins=["*"])
