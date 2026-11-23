"""English fallbacks for flag and alert codes. The client shows its own translation first."""

from typing import Any

_TEMPLATES: dict[str, str] = {
    "name_mismatch": "Name differs between {documents}: {values}.",
    "dob_mismatch": "Date of birth differs between {documents}: {values}.",
    "account_mismatch": "Passbooks show different accounts: {accounts}.",
    "nominee_missing": "No nominee registered; the legal-heir route is needed.",
    "death_within_lien_period": (
        "Natural death {days_since_enrolment} days after enrolment, within the "
        "{lien_days}-day lien period; PMJJBY is not payable."
    ),
    "rupay_no_recent_txn": "No card transaction in the {lookback_days} days before the accident.",
    "rupay_txn_unverifiable": "Only UPI/AEPS activity seen; the bank must confirm card use.",
    "accident_docs_missing": "Accident claims need these documents: {missing}.",
    "claim_window_closing": "{scheme} deadline is in {days_left} days ({due_date}).",
    "claim_window_passed": (
        "{scheme} preferred window passed {days_late} days ago; explain the delay."
    ),
    "ocr_low_confidence": "Please check the details read from the {document}.",
    "alert.cover_lapsed": "This cover has lapsed.",
    "alert.rupay_expiring": (
        "RuPay cover lapses in {days_left} days. Make one ATM, POS or BC card transaction."
    ),
    "alert.nominee_missing": "No nominee registered on this account.",
    "alert.cover_active": "Cover is active.",
}


def _render(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v).replace("_", " ") for v in value)
    return str(value)


def message_for(code: str, params: dict[str, Any]) -> str:
    template = _TEMPLATES.get(code, code)
    try:
        return template.format(**{k: _render(v) for k, v in params.items()})
    except (KeyError, IndexError):
        return template
