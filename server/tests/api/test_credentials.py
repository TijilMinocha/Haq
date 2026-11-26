"""Audit items 5-8: PIN guessing, how secrets are stored, and the operator JWT."""

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.security import decode_operator_jwt, hash_case_token
from app.services import auth_service, case_service
from app.services.case_service import IP_ATTEMPT_FACTOR

from .conftest import app_client, create_case, login

# The JWT helpers read the cached settings, so forged tokens must use the same secret.
SECRET = get_settings().jwt_secret
# The 31 characters a case code can hold, so each attempt can name a code nobody has.
_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _codes(count: int) -> list[str]:
    return [
        f"HAQ-{_ALPHABET[i // 31 % 31]}{_ALPHABET[i % 31]}2{_ALPHABET[(i + 7) % 31]}"
        for i in range(count)
    ]


async def _resume(client: AsyncClient, code: str, pin: str) -> Any:
    return await client.post("/cases/resume", json={"case_code": code, "pin": pin})


async def test_a_wrong_pin_and_an_unknown_code_are_indistinguishable() -> None:
    async with app_client() as (_, client):
        created = await create_case(client, pin="4321")
        wrong = await _resume(client, created["case_code"], "0000")
        unknown = await _resume(client, "HAQ-2222", "0000")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    # Nothing in the message says whether the code or the PIN was the wrong one.
    assert wrong.json()["error"]["code"] == "invalid_credentials"


async def test_an_unknown_case_code_still_costs_a_password_hash(
    monkeypatch: Any,
) -> None:
    seen: list[str] = []

    def spy(secret_hash: str, secret: str) -> bool:
        seen.append(secret_hash)
        return False

    monkeypatch.setattr(case_service, "verify_secret", spy)
    async with app_client() as (_, client):
        await _resume(client, "HAQ-2222", "0000")
    # Skipping the hash for a code that does not exist would make it measurably faster.
    assert seen == [case_service.DECOY_SECRET_HASH]


async def test_an_unknown_email_still_costs_a_password_hash(monkeypatch: Any) -> None:
    seen: list[str] = []

    def spy(secret_hash: str, secret: str) -> bool:
        seen.append(secret_hash)
        return False

    monkeypatch.setattr(auth_service, "verify_secret", spy)
    async with app_client() as (_, client):
        res = await client.post("/auth/login", json={"email": "nobody@haq.demo", "password": "x"})
    assert res.status_code == 401
    assert seen == [auth_service.DECOY_SECRET_HASH]


async def test_guesses_spread_across_many_case_codes_are_throttled_per_ip() -> None:
    async with app_client(lockout_attempts=5) as (_, client):
        limit = 5 * IP_ATTEMPT_FACTOR
        codes = _codes(limit + 1)
        assert len(set(codes)) == len(codes)
        for code in codes[:limit]:
            # A failed guess on a different code each time: no single code is near its limit.
            assert (await _resume(client, code, "0000")).status_code == 401
        blocked = await _resume(client, codes[limit], "0000")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "too_many_attempts"


async def test_a_correct_pin_clears_the_counters() -> None:
    async with app_client(lockout_attempts=2) as (_, client):
        limit = 2 * IP_ATTEMPT_FACTOR
        created = await create_case(client, pin="4321")
        first = _codes(2)
        for code in first:
            assert (await _resume(client, code, "0000")).status_code == 401
        resumed = await _resume(client, created["case_code"], "4321")
        assert resumed.status_code == 200

        # Both counters start again from zero, so the full budget is available once more.
        fresh = _codes(limit + 3)[2:]
        assert len(fresh) == limit + 1
        for code in fresh[:limit]:
            assert (await _resume(client, code, "0000")).status_code == 401
        blocked = await _resume(client, fresh[limit], "0000")
    assert blocked.status_code == 429


async def test_case_token_and_pin_are_stored_hashed() -> None:
    async with app_client() as (container, client):
        created = await create_case(client, pin="4321")
        record = await container.cases.get(created["case_id"])
    assert record is not None
    assert created["access_token"] not in record.token_hashes
    assert hash_case_token(created["access_token"]) in record.token_hashes
    assert "4321" not in record.pin_hash
    assert record.pin_hash.startswith("$argon2")


async def test_operator_token_expires_after_the_configured_hours() -> None:
    async with app_client() as (_, client):
        token = await login(client)
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    issued = datetime.fromtimestamp(claims["iat"], UTC)
    expires = datetime.fromtimestamp(claims["exp"], UTC)
    assert expires - issued == timedelta(hours=get_settings().jwt_expiry_hours)


async def test_an_expired_operator_token_is_rejected() -> None:
    async with app_client() as (_, client):
        operator_id = decode_operator_jwt(await login(client))
        assert operator_id is not None
        now = datetime.now(UTC)
        stale = jwt.encode(
            {
                "sub": operator_id,
                "iat": now - timedelta(hours=2),
                "exp": now - timedelta(hours=1),
            },
            SECRET,
            algorithm="HS256",
        )
        res = await client.get("/auth/me", headers={"Authorization": f"Bearer {stale}"})
    assert (res.status_code, res.json()["error"]["code"]) == (401, "invalid_token")


async def test_unsigned_and_foreign_algorithm_tokens_are_rejected() -> None:
    async with app_client() as (_, client):
        operator_id = decode_operator_jwt(await login(client))
        assert operator_id is not None
        claims = {
            "sub": operator_id,
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        }
        unsigned = jwt.encode(claims, key="", algorithm="none")
        # A token that claims RS256 but carries an HS256 signature: the confusion attack.
        confused = _hand_signed({"alg": "RS256", "typ": "JWT"}, claims, SECRET)
        wrong_key = jwt.encode(claims, "a-wrong-key-that-is-long-enough-32", algorithm="HS256")
        for token in (unsigned, confused, wrong_key):
            res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert (res.status_code, res.json()["error"]["code"]) == (401, "invalid_token")


def _hand_signed(header: dict[str, str], payload: dict[str, Any], secret: str) -> str:
    def enc(data: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    head, body = enc(header), enc(payload)
    signature = hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"
