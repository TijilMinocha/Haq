import asyncio
import os
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from alembic import command
from app.core.config import Settings
from app.infra.db.engine import make_engine
from app.main import create_app

SERVER_DIR = Path(__file__).resolve().parents[2]
TABLES = "auth_failures, case_tokens, documents, cases, operators"

AppFactory = Callable[[], AbstractAsyncContextManager[AsyncClient]]


def _database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set; Postgres integration tests skipped")
    return url


async def _ensure_database(url: str) -> None:
    parts = urlsplit(url.replace("+asyncpg", ""))
    name = parts.path.lstrip("/")
    admin = urlunsplit(parts._replace(path="/postgres"))
    conn = await asyncpg.connect(admin)
    try:
        if not await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", name):
            await conn.execute(f'CREATE DATABASE "{name}"')
    finally:
        await conn.close()


def _alembic(url: str) -> Config:
    config = Config(str(SERVER_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    config.attributes["database_url"] = url
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _database_url()
    asyncio.run(_ensure_database(url))
    config = _alembic(url)
    # Round-trip the migration so the downgrade path is exercised too.
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return url


@pytest.fixture
async def clean_db(database_url: str) -> AsyncIterator[str]:
    engine = make_engine(database_url)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    await engine.dispose()
    yield database_url


@pytest.fixture
def app_instance(clean_db: str) -> AppFactory:
    """Each call starts a fresh app on the same database, like a server restart or a
    second instance."""

    @asynccontextmanager
    async def start() -> AsyncIterator[AsyncClient]:
        app = create_app(
            Settings(env="test", storage="postgres", database_url=clean_db, extractor="mock")
        )
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
                yield c

    return start
