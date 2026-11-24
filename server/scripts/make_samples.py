"""Renders synthetic document photos for the demo scenarios, with the fields each should yield.

Run from server/:  uv run python -m scripts.make_samples
The output is deterministic, so the mock extractor can recognise the files by hash.
All people, accounts and card numbers are invented.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pymupdf

OUT = Path(__file__).resolve().parents[1] / "app" / "services" / "stubs" / "samples"
_DPI = 150
_SKEW_DEG = 2.0
_NOISE_SIGMA = 6.0


@dataclass(frozen=True)
class Sample:
    name: str
    kind: str
    lines: list[str]
    fields: dict[str, Any]
    width_pt: int = 620


def txn(day: str, narration: str, amount: int, direction: str) -> dict[str, Any]:
    return {
        "date": day,
        "narration": narration,
        "amount": amount,
        "direction": direction,
        "channel": "OTHER",
    }


def table(rows: list[tuple[str, str, str, str, str]]) -> list[str]:
    head = f"{'Date':<12}{'Particulars':<24}{'Withdrawal':>12}{'Deposit':>12}{'Balance':>12}"
    return [head, *(f"{d:<12}{p:<24}{w:>12}{c:>12}{b:>12}" for d, p, w, c, b in rows)]


SAMPLES = [
    Sample(
        "sunita_passbook",
        "passbook",
        [
            "STATE BANK OF INDIA",
            "Branch: SEELAMPUR      IFSC: SBIN0001234",
            "Name: RAMESH KUMAR",
            "A/c No: 00000031234564417",
            "Nominee: SUNITA DEVI",
            "",
            *table(
                [
                    ("01-05-2026", "BALANCE B/F", "", "", "5,000.00"),
                    ("28-05-2026", "PMJJBY PREMIUM", "436.00", "", "4,564.00"),
                    ("30-05-2026", "PMSBY PREMIUM", "20.00", "", "4,544.00"),
                    ("02-10-2026", "BY CASH", "", "3,000.00", "7,544.00"),
                    ("30-10-2026", "ATM WDL SEELAMPUR", "2,000.00", "", "5,544.00"),
                ]
            ),
        ],
        {
            "account_holder": "Ramesh Kumar",
            "bank": "SBI",
            "branch": "SEELAMPUR",
            "ifsc": "SBIN0001234",
            "account_last4": "4417",
            "nominee_name": "Sunita Devi",
            "transactions": [
                txn("2026-05-28", "PMJJBY PREMIUM", 436, "debit"),
                txn("2026-05-30", "PMSBY PREMIUM", 20, "debit"),
                txn("2026-10-02", "BY CASH", 3000, "credit"),
                txn("2026-10-30", "ATM WDL SEELAMPUR", 2000, "debit"),
            ],
        },
    ),
    Sample(
        "sunita_death_certificate",
        "death_certificate",
        [
            "GOVERNMENT OF NCT OF DELHI",
            "DEATH CERTIFICATE",
            "",
            "Name of Deceased: RAMES KUMAR",
            "Sex: MALE",
            "Age: 42",
            "Date of Death: 15-11-2026",
            "Place of Death: GTB HOSPITAL DELHI",
            "Registration No: D-2026-118842",
            "Date of Registration: 18-11-2026",
        ],
        {
            "deceased_name": "Rames Kumar",
            "date_of_death": "2026-11-15",
            "age": 42,
            "place_of_death": "GTB HOSPITAL DELHI",
            "registration_number": "D-2026-118842",
        },
        width_pt=480,
    ),
    Sample(
        "sunita_rupay_card",
        "rupay_card",
        [
            "STATE BANK OF INDIA",
            "RuPay Debit",
            "",
            "6073 9212 3456 4417",
            "VALID FROM 02/19   VALID THRU 02/29",
            "RAMESH KUMAR",
        ],
        {
            "card_bin": "607392",
            "card_last4": "4417",
            "valid_from": "2019-02-01",
            "name": "Ramesh Kumar",
        },
        width_pt=360,
    ),
    Sample(
        "sunita_aadhaar",
        "aadhaar_deceased",
        [
            "UNIQUE IDENTIFICATION AUTHORITY OF INDIA",
            "GOVERNMENT OF INDIA",
            "",
            "To,",
            "RAMESH KUMAR",
            "S/O SH. OM PRAKASH",
            "HOUSE NO 42, GALI NO 3",
            "SEELAMPUR, NORTH EAST DELHI, 110053",
            "",
            "DOB: 12/03/1984        Gender: MALE",
            "",
            "XXXX-XXXX-8921",
            "Mera Aadhaar, Meri Pehchan",
        ],
        {
            "name": "Ramesh Kumar",
            "date_of_birth": "1984-03-12",
            "gender": "M",
            "aadhaar_masked": "XXXX-XXXX-8921",
        },
        width_pt=380,
    ),
    Sample(
        "sunita_nominee_bank_proof",
        "nominee_bank_proof",
        [
            "STATE BANK OF INDIA",
            "Branch: SEELAMPUR      IFSC: SBIN0001234",
            "SAVINGS BANK ACCOUNT PASSBOOK",
            "",
            "Account Holder: SUNITA DEVI",
            "W/O LATE RAMESH KUMAR",
            "A/c No: 00000039812459844",
            "Date of Issue: 18-11-2026",
            "Status: ACTIVE / KYC VERIFIED",
        ],
        {
            "name": "Sunita Devi",
            "date": "2026-11-18",
            "reference_number": "SBIN0001234-9844",
            "notes": "SBI Savings Bank Nominee Passbook Proof",
        },
        width_pt=420,
    ),
    Sample(
        "sunita_aadhaar_nominee",
        "aadhaar_nominee",
        [
            "UNIQUE IDENTIFICATION AUTHORITY OF INDIA",
            "GOVERNMENT OF INDIA",
            "",
            "To,",
            "SUNITA DEVI",
            "W/O LATE RAMESH KUMAR",
            "HOUSE NO 42, GALI NO 3",
            "SEELAMPUR, NORTH EAST DELHI, 110053",
            "",
            "DOB: 05/08/1988        Gender: FEMALE",
            "",
            "XXXX-XXXX-3419",
            "Mera Aadhaar, Meri Pehchan",
        ],
        {
            "name": "Sunita Devi",
            "date_of_birth": "1988-08-05",
            "gender": "F",
            "aadhaar_masked": "XXXX-XXXX-3419",
        },
        width_pt=380,
    ),
    Sample(
        "meena_passbook",
        "passbook",
        [
            "PUNJAB NATIONAL BANK",
            "Branch: MANGOLPURI      IFSC: PUNB0123400",
            "Name: SURESH YADAV",
            "A/c No: 0123000100009021",
            "Nominee: MEENA YADAV",
            "",
            *table(
                [
                    ("01-06-2026", "BALANCE B/F", "", "", "2,000.00"),
                    ("20-06-2026", "PMJJBY RENEWAL PREM", "436.00", "", "1,564.00"),
                    ("25-06-2026", "UPI/P2M/KIRANA", "340.00", "", "1,224.00"),
                ]
            ),
        ],
        {
            "account_holder": "Suresh Yadav",
            "bank": "PNB",
            "branch": "MANGOLPURI",
            "ifsc": "PUNB0123400",
            "account_last4": "9021",
            "nominee_name": "Meena Yadav",
            "transactions": [
                txn("2026-06-20", "PMJJBY RENEWAL PREM", 436, "debit"),
                txn("2026-06-25", "UPI/P2M/KIRANA", 340, "debit"),
            ],
        },
    ),
    Sample(
        "raju_passbook",
        "passbook",
        [
            "STATE BANK OF INDIA",
            "Branch: OKHLA      IFSC: SBIN0005678",
            "Name: RAJU PRASAD",
            "A/c No: 00000039876547730",
            "Nominee: NOT REGISTERED",
            "",
            *table(
                [
                    ("01-05-2025", "BALANCE B/F", "", "", "10,000.00"),
                    ("29-05-2025", "PMJJBY PREMIUM", "436.00", "", "9,564.00"),
                    ("30-05-2026", "PMSBY PREMIUM", "20.00", "", "9,544.00"),
                    ("06-09-2026", "POS KIRANA STORE", "650.00", "", "8,894.00"),
                    ("02-11-2026", "UPI/P2P/RAMU", "500.00", "", "8,394.00"),
                ]
            ),
        ],
        {
            "account_holder": "Raju Prasad",
            "bank": "SBI",
            "branch": "OKHLA",
            "ifsc": "SBIN0005678",
            "account_last4": "7730",
            "nominee_name": None,
            "transactions": [
                txn("2025-05-29", "PMJJBY PREMIUM", 436, "debit"),
                txn("2026-05-30", "PMSBY PREMIUM", 20, "debit"),
                txn("2026-09-06", "POS KIRANA STORE", 650, "debit"),
                txn("2026-11-02", "UPI/P2P/RAMU", 500, "debit"),
            ],
        },
    ),
    Sample(
        "raju_rupay_card",
        "rupay_card",
        [
            "STATE BANK OF INDIA",
            "RuPay Platinum",
            "",
            "6080 3155 2210 7730",
            "VALID FROM 07/21   VALID THRU 07/31",
            "RAJU PRASAD",
        ],
        {
            "card_bin": "608031",
            "card_last4": "7730",
            "valid_from": "2021-07-01",
            "name": "Raju Prasad",
        },
        width_pt=360,
    ),
]


def render(sample: Sample) -> np.ndarray:
    line_h = 18
    height = 60 + line_h * len(sample.lines)
    doc = pymupdf.open()
    page = doc.new_page(width=sample.width_pt, height=height)
    for i, text in enumerate(sample.lines):
        page.insert_text((30, 40 + i * line_h), text, fontname="cour", fontsize=10)
    pix = page.get_pixmap(dpi=_DPI, colorspace=pymupdf.csGRAY)
    doc.close()
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w).copy()


def photograph(image: np.ndarray, seed: int) -> np.ndarray:
    """Adds the tilt, blur and sensor noise of a handheld phone photo."""
    pad = 40
    framed = cv2.copyMakeBorder(image, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
    h, w = framed.shape
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), _SKEW_DEG, 1.0)
    tilted = cv2.warpAffine(framed, matrix, (w, h), borderValue=235)
    blurred = cv2.GaussianBlur(tilted, (3, 3), 0)
    noise = np.random.default_rng(seed).normal(0, _NOISE_SIGMA, blurred.shape)
    return np.clip(blurred.astype(np.float64) + noise, 0, 255).astype(np.uint8)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for seed, sample in enumerate(SAMPLES):
        image = photograph(render(sample), seed)
        ok, png = cv2.imencode(".png", image)
        if not ok:
            raise RuntimeError(f"could not encode {sample.name}")
        (OUT / f"{sample.name}.png").write_bytes(png.tobytes())
        spec = {"kind": sample.kind, "fields": sample.fields}
        (OUT / f"{sample.name}.json").write_text(
            json.dumps(spec, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {sample.name}")


if __name__ == "__main__":
    main()
