from app.domain.models import CaseMode, DocumentKind, Scheme
from app.schemas.common import ApiModel


class SchemeInfo(ApiModel):
    scheme: Scheme
    max_amount: int
    annual_premium: int
    explanation_code: str
    required_documents: list[DocumentKind]


class Scenario(ApiModel):
    id: str
    mode: CaseMode
    title_code: str
    expected_total: int
