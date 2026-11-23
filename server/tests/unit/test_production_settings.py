import json
import logging

import pytest
from pydantic import ValidationError

from app.core.attempts import InMemoryAttemptStore
from app.core.config import DEV_SEED_PASSWORD, Settings
from app.core.logging import JsonFormatter
from app.infra.db.engine import _behind_pgbouncer
from app.infra.db.repositories import InMemoryOperatorRepository
from app.services.auth_service import AuthService

SAFE = {
    "env": "prod",
    "jwt_secret": "x" * 40,
    "database_url": "postgresql://u:p@ep-1.neon.tech/db",
}


def test_safe_production_settings_load() -> None:
    assert Settings(**SAFE).env == "prod"


@pytest.mark.parametrize(
    ("override", "problem"),
    [
        ({"jwt_secret": "short"}, "JWT_SECRET"),
        ({"storage": "memory"}, "STORAGE"),
        ({"database_url": "postgresql://haq:haq@localhost:5432/haq"}, "localhost"),
    ],
)
def test_unsafe_production_settings_refuse_to_start(override: dict[str, str], problem: str) -> None:
    with pytest.raises(ValidationError, match=problem):
        Settings(**{**SAFE, **override})


def test_seed_password_only_defaults_outside_production() -> None:
    assert Settings(env="dev").seed_password == DEV_SEED_PASSWORD
    assert Settings(**SAFE).seed_password is None
    assert Settings(**SAFE, seed_operator_password="judges-only").seed_password == "judges-only"


async def test_seeding_is_skipped_without_password() -> None:
    operators = InMemoryOperatorRepository()
    auth = AuthService(operators, InMemoryAttemptStore(5, 60), seed_password=None)
    assert await auth.seed() == 0
    assert await operators.get_by_email("mitra@haq.demo") is None


@pytest.mark.parametrize(
    ("url", "pooled"),
    [
        ("postgresql://u:p@ep-cool-1-pooler.ap-southeast-1.aws.neon.tech/db", True),
        ("postgresql://u:p@ep-cool-1.ap-southeast-1.aws.neon.tech/db", False),
        ("postgresql://u:p@aws-0-ap-south-1.pooler.supabase.com:6543/postgres", True),
        ("postgresql+asyncpg://haq:haq@localhost:5432/haq", False),
    ],
)
def test_pgbouncer_urls_are_detected(url: str, pooled: bool) -> None:
    assert _behind_pgbouncer(url) is pooled


def test_json_log_lines_carry_extras() -> None:
    record = logging.makeLogRecord(
        {"msg": "request", "levelname": "INFO", "name": "haq.access", "status": 200}
    )
    line = json.loads(JsonFormatter().format(record))
    assert (line["message"], line["status"]) == ("request", 200)
