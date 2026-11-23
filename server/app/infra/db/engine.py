from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# libpq options that hosted providers (Neon) put in their URLs but asyncpg rejects.
_DROPPED_PARAMS = frozenset({"channel_binding"})


def async_database_url(url: str) -> str:
    """Accepts a plain postgres:// URL as copied from a provider and makes it asyncpg-ready."""
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in {"postgres", "postgresql"}:
        scheme = "postgresql+asyncpg"
    params = []
    for key, value in parse_qsl(parts.query):
        if key in _DROPPED_PARAMS:
            continue
        params.append(("ssl", value) if key == "sslmode" else (key, value))
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))


def make_engine(url: str) -> AsyncEngine:
    # pre_ping survives Neon closing idle connections while the free server sleeps.
    return create_async_engine(async_database_url(url), pool_pre_ping=True, pool_size=5)


def make_sessions(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
