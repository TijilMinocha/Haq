import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()
_JWT_ALG = "HS256"
# Unambiguous alphabet: no 0/O or 1/I/L, since families read the code aloud.
_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
# Verifying against a real hash when no record exists keeps a failed lookup as slow as a
# real one, so response time cannot tell an attacker which codes or emails are registered.
DECOY_SECRET_HASH = _hasher.hash(secrets.token_urlsafe(16))


def hash_secret(secret: str) -> str:
    return _hasher.hash(secret)


def verify_secret(secret_hash: str, secret: str) -> bool:
    try:
        return _hasher.verify(secret_hash, secret)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_case_token() -> str:
    return secrets.token_urlsafe(32)


def hash_case_token(token: str) -> str:
    # Tokens are high-entropy, so a fast hash is enough and keeps every request cheap.
    return hashlib.sha256(token.encode()).hexdigest()


def token_matches(token: str, known: set[str]) -> bool:
    """Whether the token is one of the stored digests, in time that does not depend on it."""
    digest = hash_case_token(token)
    matched = False
    for candidate in known:
        # No early exit: a wrong token costs the same against every stored digest.
        matched |= hmac.compare_digest(digest, candidate)
    return matched


def new_case_code() -> str:
    return "HAQ-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(4))


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def issue_operator_jwt(operator_id: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": operator_id,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_JWT_ALG)


def decode_operator_jwt(token: str) -> str | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[_JWT_ALG])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None
