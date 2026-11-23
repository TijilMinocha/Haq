"""Name and date comparison across documents written in Hindi or English."""

import re
from dataclasses import dataclass

from indic_transliteration import sanscript
from rapidfuzz import fuzz

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_NON_LETTER = re.compile(r"[^a-z ]+")
_SPACES = re.compile(r"\s+")
# Prefixes that appear on certificates and passbooks but are not part of the name.
_HONORIFICS = frozenset(
    {
        "shri",
        "sri",
        "shree",
        "smt",
        "shrimati",
        "late",
        "lt",
        "mr",
        "mrs",
        "ms",
        "kumari",
        "km",
        "sh",
        "dr",
        "swargiya",
        "sw",
    }
)


def is_devanagari(text: str) -> bool:
    return bool(_DEVANAGARI.search(text))


def normalise_name(name: str) -> str:
    text = name
    if is_devanagari(text):
        text = sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
    text = _NON_LETTER.sub(" ", text.lower())
    words = [w for w in _SPACES.split(text) if w and w not in _HONORIFICS]
    return " ".join(words)


@dataclass(frozen=True)
class NameComparison:
    same: bool
    score: float


def compare_names(a: str, b: str, threshold: int) -> NameComparison:
    """Same-script names must match exactly after normalising, because banks reject any
    spelling difference. Across scripts, transliteration is inexact, so a fuzzy score is used.
    """
    left, right = normalise_name(a), normalise_name(b)
    score = fuzz.token_sort_ratio(left, right)
    if is_devanagari(a) != is_devanagari(b):
        return NameComparison(same=score >= threshold, score=score)
    return NameComparison(same=sorted(left.split()) == sorted(right.split()), score=score)
