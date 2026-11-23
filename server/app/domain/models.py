from enum import StrEnum


class CaseMode(StrEnum):
    CLAIM = "claim"
    PROTECT = "protect"


class Language(StrEnum):
    EN = "en"
    HI = "hi"


class EventType(StrEnum):
    NATURAL_DEATH = "natural_death"
    ACCIDENTAL_DEATH = "accidental_death"
    ACCIDENTAL_DISABILITY = "accidental_disability"


class Scheme(StrEnum):
    PMJJBY = "PMJJBY"
    PMSBY = "PMSBY"
    RUPAY_PMJDY = "RUPAY_PMJDY"


class CoverStatus(StrEnum):
    ELIGIBLE = "eligible"
    LIKELY_ELIGIBLE = "likely_eligible"
    NEEDS_VERIFICATION = "needs_verification"
    LAPSED = "lapsed"
    INELIGIBLE = "ineligible"
    NOT_FOUND = "not_found"


class DocumentKind(StrEnum):
    PASSBOOK = "passbook"
    DEATH_CERTIFICATE = "death_certificate"
    AADHAAR_DECEASED = "aadhaar_deceased"
    AADHAAR_NOMINEE = "aadhaar_nominee"
    FIR = "fir"
    POSTMORTEM = "postmortem"
    DISABILITY_CERTIFICATE = "disability_certificate"
    NOMINEE_BANK_PROOF = "nominee_bank_proof"
    RUPAY_CARD = "rupay_card"


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    UNREADABLE = "unreadable"
    CORRECTED = "corrected"


class FlagSeverity(StrEnum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class TxnChannel(StrEnum):
    ATM = "ATM"
    MICRO_ATM = "MICRO_ATM"
    POS = "POS"
    ECOM = "ECOM"
    BC = "BC"
    UPI = "UPI"
    AEPS = "AEPS"
    NEFT = "NEFT"
    CASH = "CASH"
    OTHER = "OTHER"


ELIGIBLE_LIKE: frozenset[CoverStatus] = frozenset(
    {CoverStatus.ELIGIBLE, CoverStatus.LIKELY_ELIGIBLE, CoverStatus.NEEDS_VERIFICATION}
)
