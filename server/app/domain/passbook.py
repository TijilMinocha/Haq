"""Reads insurance facts out of passbook lines: premium debits, card use, cover years."""

from collections.abc import Iterable
from datetime import date

from app.domain.config.loader import MonthDay, PremiumScheme, RulesConfig
from app.domain.facts import Txn
from app.domain.models import TxnChannel


def channel_of(txn: Txn, config: RulesConfig) -> TxnChannel:
    if txn.channel is not TxnChannel.OTHER:
        return txn.channel
    narration = txn.narration.upper()
    for channel, patterns in config.channel_patterns:
        if any(p in narration for p in patterns):
            return channel
    return TxnChannel.OTHER


def is_premium(txn: Txn, scheme: PremiumScheme) -> bool:
    # Both pattern and amount must match: the short patterns (SBY, JJBY) are too loose alone.
    narration = txn.narration.upper()
    return (
        txn.is_debit
        and txn.amount in scheme.premium_amounts
        and any(p in narration for p in scheme.narration_patterns)
    )


def premiums(txns: Iterable[Txn], scheme: PremiumScheme) -> list[Txn]:
    return sorted((t for t in txns if is_premium(t, scheme)), key=lambda t: t.date)


def cover_year_of(day: date, start: MonthDay) -> int:
    """The calendar year in which the cover year containing `day` began."""
    return day.year if day >= start.in_year(day.year) else day.year - 1


def year_paid_by(debit: date, scheme: PremiumScheme, start: MonthDay) -> int:
    """The cover year a premium debit pays for.

    Renewal debits land a few days before the cover year starts, so they pay for the
    coming year rather than the one that is ending.
    """
    if scheme.renewal_from.in_year(debit.year) <= debit < start.in_year(debit.year):
        return debit.year
    return cover_year_of(debit, start)


def card_txns_between(
    txns: Iterable[Txn],
    start: date,
    end: date,
    channels: frozenset[TxnChannel],
    config: RulesConfig,
) -> list[Txn]:
    return sorted(
        (t for t in txns if start <= t.date <= end and channel_of(t, config) in channels),
        key=lambda t: t.date,
    )
