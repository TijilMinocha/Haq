"""Reads insurance facts out of passbook lines: premium debits, card use, cover years."""

import re
from collections.abc import Iterable
from datetime import date

from app.domain.config.loader import MonthDay, PremiumScheme, RulesConfig
from app.domain.facts import Txn
from app.domain.models import TxnChannel

_ALNUM = re.compile(r"[A-Z0-9]")


def _has_token(narration: str, pattern: str) -> bool:
    """True when `pattern` appears in `narration` without a letter or digit touching it.

    Plain substring search made "DEPOSIT" a POS transaction and "BATMAN" an ATM one, so a
    cash deposit counted as card use and the RuPay cover looked active when it was not. A
    side only needs a boundary when the pattern itself ends in a letter or digit there,
    which is what keeps punctuated patterns like "BC/" and "E-COM" working.
    """
    left = _ALNUM.match(pattern[0]) is not None
    right = _ALNUM.match(pattern[-1]) is not None
    start = narration.find(pattern)
    while start != -1:
        end = start + len(pattern)
        before = narration[start - 1] if start else ""
        after = narration[end] if end < len(narration) else ""
        if (not left or not _ALNUM.match(before)) and (not right or not _ALNUM.match(after)):
            return True
        start = narration.find(pattern, start + 1)
    return False


def channel_of(txn: Txn, config: RulesConfig) -> TxnChannel:
    if txn.channel is not TxnChannel.OTHER:
        return txn.channel
    narration = txn.narration.upper()
    for channel, patterns in config.channel_patterns:
        if any(_has_token(narration, p) for p in patterns):
            return channel
    return TxnChannel.OTHER


def is_premium(txn: Txn, scheme: PremiumScheme) -> bool:
    # Both pattern and amount must match: the short patterns (SBY, JJBY) are too loose alone.
    narration = txn.narration.upper()
    return (
        txn.is_debit
        and txn.amount in scheme.premium_amounts
        and any(_has_token(narration, p) for p in scheme.narration_patterns)
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
    # Debits only: a refund credited under a POS narration says nothing about the card being
    # used by the holder, and counting it would promise cover the bank will refuse.
    return sorted(
        (
            t
            for t in txns
            if start <= t.date <= end and t.is_debit and channel_of(t, config) in channels
        ),
        key=lambda t: t.date,
    )
