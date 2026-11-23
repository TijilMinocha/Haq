from datetime import date

from app.infra.extractors.parsers import aadhaar, card, death_certificate, generic
from app.infra.extractors.pipeline import _mask_lines
from app.schemas.document import (
    CardFields,
    DeathCertificateFields,
    GenericFields,
    IdentityFields,
)

from .helpers import expected, page


def test_death_certificate() -> None:
    result = death_certificate.parse(
        page(
            """
            GOVERNMENT OF NCT OF DELHI
            DEATH CERTIFICATE
            Name of Deceased: RAMES KUMAR
            Sex: MALE
            Age: 42
            Date of Death: 15-11-2026
            Place of Death: GTB HOSPITAL DELHI
            Registration No: D-2026-118842
            Date of Registration: 18-11-2026
            """
        )
    )
    want = DeathCertificateFields.model_validate(expected("sunita_death_certificate")["fields"])
    assert result.fields == want


def test_bilingual_death_certificate_labels() -> None:
    fields = death_certificate.parse(
        page(
            """
            नाम / Name : RAMESH KUMAR
            मृत्यु की तिथि / Date of Death : 15/11/2026
            """
        )
    ).fields
    assert isinstance(fields, DeathCertificateFields)
    assert (fields.deceased_name, fields.date_of_death) == ("Ramesh Kumar", date(2026, 11, 15))


def test_aadhaar_front() -> None:
    masked = _mask_lines(
        page(
            """
            भारत सरकार
            Government of India
            रमेश कुमार
            Ramesh Kumar
            जन्म तिथि/DOB: 12/03/1984
            पुरुष / MALE
            1234 5678 9012
            """
        )
    )
    result = aadhaar.parse(masked)
    assert result.fields == IdentityFields(
        name="Ramesh Kumar",
        date_of_birth=date(1984, 3, 12),
        gender="male",
        aadhaar_masked="XXXX-XXXX-9012",
    )
    assert "1234 5678" not in " ".join(line.text for line in masked.lines)


def test_rupay_card_keeps_only_bin_and_last_four() -> None:
    masked = _mask_lines(
        page(
            """
            STATE BANK OF INDIA
            RuPay Debit
            6073 9212 3456 4417
            VALID FROM 02/19 VALID THRU 02/29
            RAMESH KUMAR
            """
        )
    )
    result = card.parse(masked)
    assert result.fields == CardFields.model_validate(expected("sunita_rupay_card")["fields"])


def test_generic_fir() -> None:
    fields = generic.parse(
        page(
            """
            FIRST INFORMATION REPORT
            FIR No: 118/2026 Police Station: SEELAMPUR
            Date: 15-11-2026
            Name of Deceased: RAMESH KUMAR
            """
        )
    ).fields
    assert fields == GenericFields(
        name="Ramesh Kumar", date=date(2026, 11, 15), reference_number="118/2026"
    )
