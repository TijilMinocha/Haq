from typing import Any

from app.domain.config.loader import load_config
from app.domain.models import DocumentKind, Scheme
from app.schemas.meta import SchemeInfo


def _max_amount(scheme: Scheme, block: dict[str, Any]) -> int:
    match scheme:
        case Scheme.PMJJBY:
            return int(block["sum_assured"])
        case Scheme.PMSBY:
            return int(block["death_or_total_disability"])
        case Scheme.RUPAY_PMJDY:
            return int(max(block["sum_insured"].values()))


def scheme_info() -> list[SchemeInfo]:
    schemes: dict[str, dict[str, Any]] = load_config()["schemes"]
    return [
        SchemeInfo(
            scheme=Scheme(name),
            max_amount=_max_amount(Scheme(name), block),
            annual_premium=int(block.get("premium_amounts", [0])[0]),
            explanation_code=f"schemes.{name}.explanation",
            required_documents=[DocumentKind(k) for k in block.get("documents", [])],
        )
        for name, block in schemes.items()
    ]
