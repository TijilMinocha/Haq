from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.domain.models import DocumentKind
from app.infra.extractors.base import ExtractionResult, ExtractorUnavailable, UnreadableDocument
from app.infra.extractors.mock import SAMPLES_DIR
from app.main import create_app


def _sample(name: str) -> bytes:
    return Path(SAMPLES_DIR / f"{name}.png").read_bytes()


async def _upload(
    client: AsyncClient, case_id: str, headers: dict[str, str], kind: str, content: bytes
) -> dict[str, object]:
    res = await client.post(
        f"/cases/{case_id}/documents",
        headers=headers,
        data={"kind": kind},
        files={"file": (f"{kind}.png", content, "image/png")},
    )
    assert res.status_code == 200, res.text
    body: dict[str, object] = res.json()
    return body


async def test_sunita_from_photos_to_six_lakh(client: AsyncClient) -> None:
    created = (await client.post("/cases", json={"mode": "claim", "pin": "1234"})).json()
    case_id, headers = created["case_id"], {"X-Case-Token": created["access_token"]}
    await client.patch(
        f"/cases/{case_id}",
        headers=headers,
        json={
            "subject": {"name": "Ramesh Kumar"},
            "event": {"type": "accidental_death", "date": "2026-11-15"},
            "nominee": {"name": "Sunita Devi", "relation": "wife"},
        },
    )
    await _upload(client, case_id, headers, "passbook", _sample("sunita_passbook"))
    await _upload(client, case_id, headers, "rupay_card", _sample("sunita_rupay_card"))
    view = await _upload(
        client, case_id, headers, "death_certificate", _sample("sunita_death_certificate")
    )

    evaluation = view["evaluation"]
    assert isinstance(evaluation, dict)
    assert evaluation["total_claimable"] == 600000
    assert "name_mismatch" in {f["code"] for f in evaluation["flags"]}
    documents = view["documents"]
    assert isinstance(documents, list)
    card = next(d for d in documents if d["kind"] == "rupay_card")
    assert card["fields"]["card_bin"] == "607392"
    assert "card_number" not in card["fields"]


class _Failing:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def extract(
        self, content: bytes, content_type: str, kind: DocumentKind
    ) -> ExtractionResult:
        raise self._error


@asynccontextmanager
async def _client_with(error: Exception) -> AsyncIterator[AsyncClient]:
    app = create_app(Settings(env="test", storage="memory"), extractor=_Failing(error))
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1") as c,
    ):
        yield c


async def _try_upload(client: AsyncClient) -> tuple[int, str]:
    created = (await client.post("/cases", json={"mode": "claim", "pin": "1234"})).json()
    res = await client.post(
        f"/cases/{created['case_id']}/documents",
        headers={"X-Case-Token": created["access_token"]},
        data={"kind": "passbook"},
        files={"file": ("p.png", b"\x89PNG", "image/png")},
    )
    return res.status_code, res.json()["error"]["code"]


async def test_unreadable_photo_asks_for_retake() -> None:
    async with _client_with(UnreadableDocument("blurry")) as client:
        assert await _try_upload(client) == (422, "document_unreadable")


async def test_missing_ocr_engine_offers_retry() -> None:
    async with _client_with(ExtractorUnavailable("no tesseract")) as client:
        assert await _try_upload(client) == (503, "extractor_unavailable")


async def test_corrections_are_masked(client: AsyncClient) -> None:
    created = (await client.post("/cases", json={"mode": "claim", "pin": "1234"})).json()
    case_id, headers = created["case_id"], {"X-Case-Token": created["access_token"]}
    view = await _upload(client, case_id, headers, "fir", b"\xff\xd8fake")
    documents = view["documents"]
    assert isinstance(documents, list)
    res = await client.patch(
        f"/cases/{case_id}/documents/{documents[0]['id']}",
        headers=headers,
        json={"fields": {"notes": "aadhaar 1234 5678 9012"}},
    )
    assert res.json()["documents"][0]["fields"]["notes"] == "aadhaar XXXX-XXXX-9012"
