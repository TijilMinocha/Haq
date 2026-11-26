from functools import lru_cache
from typing import Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-change-me-dev-only-change-me"
# Matches the documented demo logins; never used when ENV=prod.
DEV_SEED_PASSWORD = "haq-demo-2026"
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    storage: Literal["postgres", "memory"] = "postgres"
    database_url: str = "postgresql+asyncpg://haq:haq@localhost:5432/haq"
    jwt_secret: str = DEV_JWT_SECRET
    jwt_expiry_hours: int = 12
    extractor: Literal["tesseract", "mock"] = "tesseract"
    # OCR passes in order; see TesseractExtractor for why English runs first.
    ocr_languages: str = "eng,hin+eng"
    # Only needed on Windows when tesseract.exe is not on PATH.
    tesseract_cmd: str | None = None
    # Below this, the user is asked to retake the photo instead of correcting fields.
    extract_min_confidence: float = 0.35
    cors_origins: list[str] = ["http://localhost:5173"]
    # Lets Vercel preview deployments call the API, e.g. https://haq-[a-z0-9-]+\.vercel\.app
    cors_origin_regex: str | None = None
    max_upload_mb: int = 8
    lockout_attempts: int = 5
    lockout_minutes: int = 15
    # Per client IP, per minute. Lockout (above) guards guessing; these guard flooding.
    rate_limit_uploads: int = 12
    rate_limit_auth: int = 30
    log_level: str = "INFO"
    log_json: bool = False
    # Password for the seeded demo Bank Mitra accounts. Required in prod to create them.
    seed_operator_password: str | None = None

    @property
    def seed_password(self) -> str | None:
        if self.seed_operator_password:
            return self.seed_operator_password
        return None if self.env == "prod" else DEV_SEED_PASSWORD

    @property
    def rate_limits_enabled(self) -> bool:
        return self.env != "test"

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard_origin(cls, origins: list[str]) -> list[str]:
        # "*" would let any site on the internet call the API with the user's session.
        if any(origin.strip() == "*" for origin in origins):
            raise ValueError('CORS_ORIGINS must list the real front-end origins, not "*"')
        return origins

    @model_validator(mode="after")
    def _safe_for_production(self) -> Self:
        if self.env != "prod":
            return self
        problems = []
        if self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < _MIN_SECRET_LENGTH:
            problems.append(f"JWT_SECRET must be a random string of {_MIN_SECRET_LENGTH}+ chars")
        if self.storage != "postgres":
            problems.append("STORAGE must be postgres")
        if "localhost" in self.database_url:
            problems.append("DATABASE_URL still points at localhost")
        if problems:
            raise ValueError("unsafe production settings: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
