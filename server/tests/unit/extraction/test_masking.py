import pytest

from app.infra.extractors.masking import mask_model, mask_text
from app.schemas.document import GenericFields


@pytest.mark.parametrize(
    ("raw", "masked"),
    [
        ("Aadhaar 1234 5678 9012", "Aadhaar XXXX-XXXX-9012"),
        ("1234-5678-9012", "XXXX-XXXX-9012"),
        ("123456789012 is mine", "XXXX-XXXX-9012 is mine"),
        ("card 6073 9212 3456 4417", "card 6073 92XX XXXX 4417"),
        ("6073921234564417", "6073 92XX XXXX 4417"),
        ("A/c 00000031234564417", "A/c 00000031234564417"),
        ("amount 4,564.00 on 28-05-2026", "amount 4,564.00 on 28-05-2026"),
    ],
)
def test_mask_text(raw: str, masked: str) -> None:
    assert mask_text(raw) == masked


def test_mask_model_masks_user_typed_fields() -> None:
    fields = GenericFields(name="Sunita", notes="her aadhaar is 1234 5678 9012")
    assert mask_model(fields).notes == "her aadhaar is XXXX-XXXX-9012"
