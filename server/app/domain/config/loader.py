from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.domain.models import DocumentKind, EventType, Scheme, TxnChannel

_CONFIG_DIR = Path(__file__).parent
CURRENT_FY = "2026_27"

DocumentsByEvent = Mapping[EventType, tuple[DocumentKind, ...]]


@dataclass(frozen=True)
class MonthDay:
    month: int
    day: int

    @classmethod
    def parse(cls, value: str) -> "MonthDay":
        month, day = value.split("-")
        return cls(int(month), int(day))

    def in_year(self, year: int) -> date:
        return date(year, self.month, self.day)


@dataclass(frozen=True)
class PremiumScheme:
    premium_amounts: frozenset[int]
    narration_patterns: tuple[str, ...]
    renewal_from: MonthDay
    claim_preferred_within_days: int
    max_cover_age: int
    documents: DocumentsByEvent


@dataclass(frozen=True)
class PmjjbyConfig(PremiumScheme):
    sum_assured: int
    lien_days: int


@dataclass(frozen=True)
class PmsbyConfig(PremiumScheme):
    death_or_total_disability: int
    partial_disability: int


@dataclass(frozen=True)
class RupayConfig:
    old_card_amount: int
    new_card_amount: int
    new_card_after: date
    eligible_bins: frozenset[str]
    txn_lookback_days: int
    counting_channels: frozenset[TxnChannel]
    unverifiable_channels: frozenset[TxnChannel]
    intimation_within_days: int
    expiry_warning_days: int
    documents: DocumentsByEvent


@dataclass(frozen=True)
class RulesConfig:
    fy: str
    cover_year_start: MonthDay
    pmjjby: PmjjbyConfig
    pmsby: PmsbyConfig
    rupay: RupayConfig
    accident_documents: DocumentsByEvent
    channel_patterns: tuple[tuple[TxnChannel, tuple[str, ...]], ...]
    name_threshold: int
    min_confidence: float
    closing_warning_days: int

    def documents_for(self, scheme: Scheme) -> DocumentsByEvent:
        return {
            Scheme.PMJJBY: self.pmjjby.documents,
            Scheme.PMSBY: self.pmsby.documents,
            Scheme.RUPAY_PMJDY: self.rupay.documents,
        }[scheme]


def _documents(raw: Mapping[str, list[str]]) -> DocumentsByEvent:
    return {EventType(k): tuple(DocumentKind(d) for d in v) for k, v in raw.items()}


def _premium_fields(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "premium_amounts": frozenset(int(a) for a in raw["premium_amounts"]),
        "narration_patterns": tuple(p.upper() for p in raw["narration_patterns"]),
        "renewal_from": MonthDay.parse(raw["renewal_debit_window"]["from"]),
        "claim_preferred_within_days": int(raw["claim_preferred_within_days"]),
        "max_cover_age": int(raw["max_cover_age"]),
        "documents": _documents(raw["documents"]),
    }


def parse_config(raw: Mapping[str, Any]) -> RulesConfig:
    schemes = raw["schemes"]
    jj, sb, rp = schemes["PMJJBY"], schemes["PMSBY"], schemes["RUPAY_PMJDY"]
    return RulesConfig(
        fy=str(raw["fy"]),
        cover_year_start=MonthDay.parse(raw["cover_year"]["start"]),
        pmjjby=PmjjbyConfig(
            **_premium_fields(jj),
            sum_assured=int(jj["sum_assured"]),
            lien_days=int(jj["lien_days"]),
        ),
        pmsby=PmsbyConfig(
            **_premium_fields(sb),
            death_or_total_disability=int(sb["death_or_total_disability"]),
            partial_disability=int(sb["partial_disability"]),
        ),
        rupay=RupayConfig(
            old_card_amount=int(rp["sum_insured"]["old_card"]),
            new_card_amount=int(rp["sum_insured"]["new_card"]),
            new_card_after=date.fromisoformat(rp["new_card_after"]),
            eligible_bins=frozenset(str(b) for b in rp["eligible_bins"]),
            txn_lookback_days=int(rp["txn_lookback_days"]),
            counting_channels=frozenset(TxnChannel(c) for c in rp["counting_channels"]),
            unverifiable_channels=frozenset(TxnChannel(c) for c in rp["unverifiable_channels"]),
            intimation_within_days=int(rp["intimation_within_days"]),
            expiry_warning_days=int(rp["expiry_warning_days"]),
            documents=_documents(rp["documents"]),
        ),
        accident_documents=_documents(raw["accident_documents"]),
        channel_patterns=tuple(
            (TxnChannel(e["channel"]), tuple(p.upper() for p in e["patterns"]))
            for e in raw["channel_patterns"]
        ),
        name_threshold=int(raw["matching"]["name_threshold"]),
        min_confidence=float(raw["matching"]["min_confidence"]),
        closing_warning_days=int(raw["deadlines"]["closing_warning_days"]),
    )


@lru_cache
def load_raw_config(fy: str = CURRENT_FY) -> dict[str, Any]:
    with (_CONFIG_DIR / f"fy{fy}.yaml").open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


@lru_cache
def load_config(fy: str = CURRENT_FY) -> RulesConfig:
    return parse_config(load_raw_config(fy))
