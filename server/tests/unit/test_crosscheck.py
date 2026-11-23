from dataclasses import replace

from app.domain.models import DocumentKind
from app.domain.rules import crosscheck

from .factories import CONFIG, claim, d, doc, passbook, protect, with_docs


def _codes(facts: object) -> list[str]:
    return [f.code for f in crosscheck.evaluate(facts, CONFIG)]  # type: ignore[arg-type]


def test_name_mismatch_against_passbook() -> None:
    facts = with_docs(claim(), doc(DocumentKind.DEATH_CERTIFICATE, name="Rames Kumar"))
    (flag,) = crosscheck.name_flags(facts, CONFIG)
    assert flag.code == "name_mismatch"
    assert flag.params == {
        "documents": ["passbook", "death_certificate"],
        "values": ["Ramesh Kumar", "Rames Kumar"],
    }


def test_matching_names_across_scripts_pass() -> None:
    facts = with_docs(claim(), doc(DocumentKind.AADHAAR_DECEASED, name="रमेश कुमार"))
    assert crosscheck.name_flags(facts, CONFIG) == []


def test_dob_mismatch() -> None:
    facts = with_docs(
        claim(),
        doc(DocumentKind.DEATH_CERTIFICATE, date_of_birth=d("1984-03-12")),
        doc(DocumentKind.AADHAAR_DECEASED, date_of_birth=d("1984-12-03")),
    )
    assert _codes(facts) == ["dob_mismatch"]


def test_account_mismatch() -> None:
    facts = claim()
    facts = replace(facts, passbooks=(*facts.passbooks, passbook(account_last4="9999")))
    assert "account_mismatch" in _codes(facts)


def test_nominee_missing_in_claim_mode() -> None:
    facts = replace(claim(passbook=passbook(nominee_name=None)), nominee_name=None)
    assert _codes(facts) == ["nominee_missing"]


def test_nominee_from_case_is_enough() -> None:
    facts = claim(passbook=passbook(nominee_name=None))
    assert _codes(facts) == []


def test_nominee_flag_is_claim_only() -> None:
    assert _codes(protect(passbook=passbook(nominee_name=None))) == []


def test_low_confidence_unless_corrected() -> None:
    low = with_docs(claim(), doc(DocumentKind.FIR, confidence=0.3))
    assert _codes(low) == ["ocr_low_confidence"]
    fixed = with_docs(claim(), doc(DocumentKind.FIR, confidence=0.3, corrected=True))
    assert _codes(fixed) == []
