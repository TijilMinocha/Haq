import datetime as dt

from pydantic import Field

from app.domain.models import DocumentKind, DocumentStatus, TxnChannel
from app.schemas.common import ApiModel


class Transaction(ApiModel):
    date: dt.date
    narration: str
    amount: int
    direction: str = Field(pattern="^(debit|credit)$")
    channel: TxnChannel = TxnChannel.OTHER


class PassbookFields(ApiModel):
    account_holder: str | None = None
    bank: str | None = None
    branch: str | None = None
    ifsc: str | None = None
    account_last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    nominee_name: str | None = None
    card_bin: str | None = Field(default=None, pattern=r"^\d{6}$")
    card_issued_on: dt.date | None = None
    transactions: list[Transaction] = []


class DeathCertificateFields(ApiModel):
    deceased_name: str | None = None
    date_of_death: dt.date | None = None
    date_of_birth: dt.date | None = None
    age: int | None = None
    place_of_death: str | None = None
    cause: str | None = None
    registration_number: str | None = None


class IdentityFields(ApiModel):
    name: str | None = None
    date_of_birth: dt.date | None = None
    gender: str | None = None
    aadhaar_masked: str | None = Field(default=None, pattern=r"^XXXX-XXXX-\d{4}$")


class GenericFields(ApiModel):
    name: str | None = None
    date: dt.date | None = None
    reference_number: str | None = None
    notes: str | None = None


DocumentFields = PassbookFields | DeathCertificateFields | IdentityFields | GenericFields


class DocumentView(ApiModel):
    id: str
    kind: DocumentKind
    status: DocumentStatus
    confidence: float = Field(ge=0, le=1)
    fields: DocumentFields


class DocumentPatch(ApiModel):
    fields: DocumentFields
