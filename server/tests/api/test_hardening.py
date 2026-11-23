from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.domain.models import DocumentKind
from app.infra.extractors.base import ExtractionResult
from app.main import create_app

ORIGIN = "http://localhost:5173"


@asynccontextmanager
async def _client(**overrides: Any) -> AsyncIterator[AsyncClient]:
    extractor = overrides.pop("_extractor", None)
    settings = Settings(**{"env": "test", "storage": "memory", "extractor": "mock", **overrides})
    app = create_app(settings, extractor=extractor)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as c,
    ):
        yield c


async def test_request_id_is_generated_or_echoed() -> None:
    async with _client() as client:
        generated = await client.get("/health")
        assert len(generated.headers["x-request-id"]) == 32
        echoed = await client.get("/health", headers={"X-Request-ID": "phone-42"})
        assert echoed.headers["x-request-id"] == "phone-42"
        unsafe = await client.get("/health", headers={"X-Request-ID": "bad id\n"})
        assert unsafe.headers["x-request-id"] != "bad id\n"


async def test_security_headers() -> None:
    async with _client() as client:
        res = await client.get("/health")
    assert res.headers["cache-control"] == "no-store"
    assert res.headers["x-content-type-options"] == "nosniff"


async def test_oversized_upload_rejected_before_reading() -> None:
    async with _client(max_upload_mb=1) as client:
        res = await client.post(
            "/cases/c_x/documents",
            content=b"x",
            headers={"Content-Length": str(3 * 1024 * 1024), "Origin": ORIGIN},
        )
    assert (res.status_code, res.json()["error"]["code"]) == (413, "file_too_large")
    assert res.headers["access-control-allow-origin"] == ORIGIN


async def test_rate_limit_returns_429_with_retry_after() -> None:
    async with _client(env="dev", rate_limit_auth=2) as client:
        for _ in range(2):
            ok = await client.post("/cases", json={"mode": "claim", "pin": "1234"})
            assert ok.status_code == 201
        res = await client.post(
            "/cases", json={"mode": "claim", "pin": "1234"}, headers={"Origin": ORIGIN}
        )
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "too_many_attempts"
        assert int(res.headers["retry-after"]) >= 1
        assert res.headers["access-control-allow-origin"] == ORIGIN
        # Other routes are not limited by the auth rule.
        assert (await client.get("/health")).status_code == 200


async def test_readiness_reports_components() -> None:
    async with _client() as client:
        res = await client.get("/health/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": True, "ocr": True}


class _Broken:
    def ready(self) -> bool:
        return False

    async def extract(
        self, content: bytes, content_type: str, kind: DocumentKind
    ) -> ExtractionResult:
        raise RuntimeError("boom")


async def test_unexpected_error_returns_request_id_with_cors() -> None:
    async with _client(_extractor=_Broken()) as client:
        created = (await client.post("/cases", json={"mode": "claim", "pin": "1234"})).json()
        res = await client.post(
            f"/cases/{created['case_id']}/documents",
            headers={"X-Case-Token": created["access_token"], "Origin": ORIGIN},
            data={"kind": "passbook"},
            files={"file": ("p.png", b"\x89PNG", "image/png")},
        )
        assert res.status_code == 500
        body = res.json()["error"]
        assert body["code"] == "internal_error"
        assert body["details"]["request_id"] == res.headers["x-request-id"]
        assert res.headers["access-control-allow-origin"] == ORIGIN
        ready = await client.get("/health/ready")
        assert (ready.status_code, ready.json()["ocr"]) == (503, False)
