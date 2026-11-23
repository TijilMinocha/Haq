import datetime as dt
from typing import Annotated

from pydantic import Field

from app.domain.models import CaseMode, EventType, Language
from app.schemas.common import ApiModel
from app.schemas.document import DocumentView
from app.schemas.evaluation import Evaluation

Pin = Annotated[str, Field(pattern=r"^\d{4}$")]
CaseCode = Annotated[str, Field(pattern=r"^HAQ-[2-9A-HJKMNP-Z]{4}$")]


class Subject(ApiModel):
    name: str | None = None
    date_of_birth: dt.date | None = None


class Event(ApiModel):
    type: EventType | None = None
    date: dt.date | None = None


class Nominee(ApiModel):
    name: str | None = None
    relation: str | None = None


class CaseView(ApiModel):
    id: str
    code: str
    mode: CaseMode
    language: Language
    subject: Subject
    event: Event
    nominee: Nominee
    documents: list[DocumentView]
    evaluation: Evaluation
    updated_at: dt.datetime


class CaseCreate(ApiModel):
    mode: CaseMode
    language: Language = Language.HI
    pin: Pin


class CaseCreated(ApiModel):
    case_id: str
    case_code: str
    access_token: str


class CaseResume(ApiModel):
    case_code: CaseCode
    pin: Pin


class CaseResumed(ApiModel):
    case_id: str
    access_token: str


class CaseUpdate(ApiModel):
    subject: Subject | None = None
    event: Event | None = None
    nominee: Nominee | None = None
    language: Language | None = None


class CaseSummary(ApiModel):
    id: str
    code: str
    mode: CaseMode
    subject_name: str | None
    total_claimable: int
    blocker_count: int
    status: str
    updated_at: dt.datetime
