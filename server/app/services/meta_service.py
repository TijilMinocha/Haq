from app.domain.config.loader import DocumentsByEvent, load_config
from app.domain.models import DocumentKind, Scheme
from app.schemas.meta import SchemeInfo


def _all_documents(by_event: DocumentsByEvent) -> list[DocumentKind]:
    return list(dict.fromkeys(kind for kinds in by_event.values() for kind in kinds))


def scheme_info() -> list[SchemeInfo]:
    config = load_config()
    rows = (
        (Scheme.PMJJBY, config.pmjjby.sum_assured, max(config.pmjjby.premium_amounts)),
        (Scheme.PMSBY, config.pmsby.death_or_total_disability, max(config.pmsby.premium_amounts)),
        (Scheme.RUPAY_PMJDY, config.rupay.new_card_amount, 0),
    )
    return [
        SchemeInfo(
            scheme=scheme,
            max_amount=max_amount,
            annual_premium=premium,
            explanation_code=f"schemes.{scheme.value}.explanation",
            required_documents=_all_documents(config.documents_for(scheme)),
        )
        for scheme, max_amount, premium in rows
    ]
