import logging

from app.core.attempts import AttemptStore
from app.core.errors import invalid_credentials
from app.core.security import hash_secret, issue_operator_jwt, new_id, verify_secret
from app.infra.db.repositories import OperatorRecord, OperatorRepository
from app.schemas.auth import LoginRequest, LoginResponse, Operator

log = logging.getLogger(__name__)

# Hackathon demo accounts; there is no public sign-up. The password here is for local
# development only: production takes it from SEED_OPERATOR_PASSWORD.
SEED_OPERATORS = (
    ("mitra@haq.demo", "Demo Bank Mitra", "haq-demo-2026"),
    ("mitra2@haq.demo", "Second Bank Mitra", "haq-demo-2026"),
)


def to_schema(record: OperatorRecord) -> Operator:
    return Operator(id=record.id, email=record.email, name=record.name)


class AuthService:
    def __init__(
        self, operators: OperatorRepository, limiter: AttemptStore, seed_password: str | None
    ) -> None:
        self._operators = operators
        self._limiter = limiter
        self._seed_password = seed_password

    async def login(self, data: LoginRequest) -> LoginResponse:
        email = data.email.strip().lower()
        await self._limiter.check(email)
        record = await self._operators.get_by_email(email)
        if record is None or not verify_secret(record.password_hash, data.password):
            await self._limiter.fail(email)
            raise invalid_credentials()
        await self._limiter.reset(email)
        return LoginResponse(access_token=issue_operator_jwt(record.id), operator=to_schema(record))

    async def seed(self) -> int:
        """Creates missing demo accounts and returns how many exist afterwards."""
        if self._seed_password is None:
            log.warning("SEED_OPERATOR_PASSWORD not set; demo Bank Mitra accounts not created")
            return 0
        for email, name, _ in SEED_OPERATORS:
            if await self._operators.get_by_email(email) is None:
                await self._operators.add(
                    OperatorRecord(
                        id=new_id("op"),
                        email=email,
                        name=name,
                        password_hash=hash_secret(self._seed_password),
                    )
                )
        return len(SEED_OPERATORS)
