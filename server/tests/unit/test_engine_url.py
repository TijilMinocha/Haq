import pytest

from app.infra.db.engine import async_database_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgresql://u:p@ep-x.neon.tech/haq?sslmode=require&channel_binding=require",
            "postgresql+asyncpg://u:p@ep-x.neon.tech/haq?ssl=require",
        ),
        ("postgres://u:p@localhost:5432/haq", "postgresql+asyncpg://u:p@localhost:5432/haq"),
        (
            "postgresql+asyncpg://haq:haq@localhost:5432/haq",
            "postgresql+asyncpg://haq:haq@localhost:5432/haq",
        ),
    ],
)
def test_provider_urls_become_asyncpg_urls(raw: str, expected: str) -> None:
    assert async_database_url(raw) == expected
