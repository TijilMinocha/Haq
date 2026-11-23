from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Coded(ApiModel):
    """User-facing text travels as a code plus params; the client translates it."""

    code: str
    params: dict[str, Any] = {}
