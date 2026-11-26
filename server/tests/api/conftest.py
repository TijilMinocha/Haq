"""Shared harness for the API tests: the client and the container it is running on."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.services.container import Container

ORIGIN = "http://localhost:5173"
HOST = "http://test/api/v1"


@asynccontextmanager
async def app_client(**overrides: Any) -> AsyncIterator[tuple[Container, AsyncClient]]:
    extractor = overrides.pop("_extractor", None)
    settings = Settings(**{"env": "test", "storage": "memory", "extractor": "mock", **overrides})
    app = create_app(settings, extractor=extractor)
    container: Container = app.state.container
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url=HOST) as client,
    ):
        yield container, client


async def create_case(client: AsyncClient, pin: str = "4321") -> dict[str, str]:
    res = await client.post("/cases", json={"mode": "claim", "language": "hi", "pin": pin})
    assert res.status_code == 201, res.text
    body: dict[str, str] = res.json()
    return body


async def login(client: AsyncClient, index: int = 0) -> str:
    from app.services.auth_service import SEED_OPERATORS

    email, _, password = SEED_OPERATORS[index]
    res = await client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    token: str = res.json()["access_token"]
    return token


async def add_document(client: AsyncClient, case_id: str, headers: dict[str, str]) -> str:
    res = await client.post(
        f"/cases/{case_id}/documents",
        headers=headers,
        data={"kind": "fir"},
        files={"file": ("fir.jpg", b"\xff\xd8photo", "image/jpeg")},
    )
    assert res.status_code == 200, res.text
    document_id: str = res.json()["documents"][-1]["id"]
    return document_id
