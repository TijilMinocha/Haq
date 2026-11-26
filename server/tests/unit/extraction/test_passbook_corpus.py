import random
import string

import pytest

from app.infra.extractors.ocr import OcrPage
from app.infra.extractors.parsers import passbook
from app.schemas.document import PassbookFields

from .helpers import page
from .passbook_corpus import AMBIGUOUS, SAMPLES, Sample, devanagari


def _param(sample: Sample) -> pytest.ParameterSet:
    reason = AMBIGUOUS.get(sample.name)
    if reason is None:
        return pytest.param(sample, id=sample.name)
    return pytest.param(sample, id=sample.name, marks=pytest.mark.xfail(reason=reason, strict=True))


@pytest.mark.parametrize("sample", [_param(s) for s in SAMPLES])
def test_corpus_sample_parses_exactly(sample: Sample) -> None:
    fields = passbook.parse(page(sample.text)).fields
    assert isinstance(fields, PassbookFields)
    assert fields.account_holder == sample.account_holder
    assert fields.bank == sample.bank
    assert fields.branch == sample.branch
    assert fields.ifsc == sample.ifsc
    assert fields.account_last4 == sample.account_last4
    assert fields.nominee_name == sample.nominee_name
    assert [
        (t.date.isoformat(), t.narration, t.amount, t.direction) for t in fields.transactions
    ] == [(e.date, e.narration, e.amount, e.direction) for e in sample.transactions]


def _scrambled_page(seed: int, lines: int = 200) -> OcrPage:
    rng = random.Random(seed)
    alphabet = string.printable + "०१२३४५६७८९|~_/-.,:"
    body = []
    for _ in range(lines):
        body.append("".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60))))
    # Real page furniture, so the parser meets wrecked dates and amounts too.
    body.insert(rng.randrange(len(body)), "28-05-2026 PMJJBY PREMIUM 436.00 4,564.00")
    body.insert(rng.randrange(len(body)), "lO-O5-2O26 4S6.OO | 4,5 64.00 |")
    body.insert(rng.randrange(len(body)), "नाम / Name : राजू प्रसाद")
    body.insert(rng.randrange(len(body)), devanagari("01-05-2026 5,000.00 43600"))
    return OcrPage.from_text("\n".join(body))


def test_never_crashes_on_scrambled_text() -> None:
    for seed in range(5):
        result = passbook.parse(_scrambled_page(seed))
        assert isinstance(result.fields, PassbookFields)
