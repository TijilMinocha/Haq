"""Aadhaar and card-number masking, applied to OCR text before anything parses, stores or
logs it."""

import re

from pydantic import BaseModel

# 12 digits in 4-4-4 groups, not part of a longer number such as a 16-digit card.
_AADHAAR = re.compile(r"(?<!\d)(?<!\d[ -])(\d{4})[ -]?(\d{4})[ -]?(\d{4})(?![ -]?\d)")
# 16 digits in 4-4-4-4 groups: keep the BIN (first 6) and last 4 only.
_CARD = re.compile(r"(?<!\d)(\d{4})[ -]?(\d{2})(\d{2})[ -]?(\d{4})[ -]?(\d{4})(?![ -]?\d)")


def mask_card(text: str) -> str:
    return _CARD.sub(lambda m: f"{m[1]} {m[2]}XX XXXX {m[5]}", text)


def mask_aadhaar(text: str) -> str:
    return _AADHAAR.sub(lambda m: f"XXXX-XXXX-{m[3]}", text)


def mask_text(text: str) -> str:
    return mask_aadhaar(mask_card(text))


def mask_model[M: BaseModel](model: M) -> M:
    """Masks every string field, including nested ones, for user-typed corrections."""
    return type(model).model_validate(_mask_value(model.model_dump(mode="json")))


def _mask_value(value: object) -> object:
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, list):
        return [_mask_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _mask_value(v) for k, v in value.items()}
    return value
