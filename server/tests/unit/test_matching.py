import pytest

from app.domain.matching import compare_names, normalise_name

THRESHOLD = 88


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Late Shri Ramesh Kumar", "ramesh kumar"),
        ("SMT. SUNITA  DEVI", "sunita devi"),
        ("Ramesh-Kumar", "ramesh kumar"),
    ],
)
def test_normalise_strips_honorifics_and_punctuation(raw: str, expected: str) -> None:
    assert normalise_name(raw) == expected


@pytest.mark.parametrize(
    ("a", "b", "same"),
    [
        ("Ramesh Kumar", "RAMESH KUMAR", True),
        ("Kumar Ramesh", "Ramesh Kumar", True),
        ("Late Ramesh Kumar", "Ramesh Kumar", True),
        ("Rames Kumar", "Ramesh Kumar", False),
        ("R. Kumar", "Ramesh Kumar", False),
        ("रमेश कुमार", "Ramesh Kumar", True),
        ("सुनीता देवी", "Sunita Devi", True),
        ("सुरेश यादव", "Ramesh Kumar", False),
    ],
)
def test_compare_names(a: str, b: str, same: bool) -> None:
    assert compare_names(a, b, THRESHOLD).same is same
