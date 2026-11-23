from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "postgresql+asyncpg://haq:haq@localhost:5432/haq"
    jwt_secret: str = "dev-only-change-me-dev-only-change-me"
    jwt_expiry_hours: int = 12
    extractor: Literal["tesseract", "gemini", "mock"] = "mock"
    gemini_api_key: str | None = None
    cors_origins: list[str] = ["http://localhost:5173"]
    max_upload_mb: int = 8
    lockout_attempts: int = 5
    lockout_minutes: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
