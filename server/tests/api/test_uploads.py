"""Audit items 9-11: what an upload may contain, where it may go, and what is masked."""

import struct
import zlib
from typing import Any

from httpx import AsyncClient

from app.domain.models import DocumentKind
from app.infra.extractors.base import ExtractionResult
from app.schemas.document import GenericFields

from .conftest import app_client, create_case

MARKER = b"MARKER-NEVER-STORE-ME"


def _png(width: int, height: int, body: bytes = b"") -> bytes:
    """A real PNG header and IHDR, so the size guard has something true to read."""
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    chunk = b"IHDR" + header
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", len(header))
        + chunk
        + struct.pack(">I", zlib.crc32(chunk))
        + body
    )


async def _upload(
    client: AsyncClient,
    case_id: str,
    headers: dict[str, str],
    content: bytes,
    content_type: str = "image/png",
    kind: str = "passbook",
) -> Any:
    return await client.post(
        f"/cases/{case_id}/documents",
        headers=headers,
        data={"kind": kind},
        files={"file": ("upload.png", content, content_type)},
    )


async def test_the_content_type_is_decided_by_the_bytes_not_the_header() -> None:
    async with app_client() as (_, client):
        created = await create_case(client)
        headers = {"X-Case-Token": created["access_token"]}
        text = await _upload(client, created["case_id"], headers, b"just some text")
        image = await _upload(client, created["case_id"], headers, _png(10, 10), "text/plain")
        pdf = await _upload(
            client, created["case_id"], headers, b"%PDF-1.4 not really", "image/jpeg"
        )
    assert (text.status_code, text.json()["error"]["code"]) == (415, "unsupported_file")
    # Real bytes are accepted whatever the client called them.
    assert image.status_code == 200
    assert pdf.status_code == 200


async def test_a_zero_byte_file_is_refused() -> None:
    async with app_client() as (_, client):
        created = await create_case(client)
        res = await _upload(
            client, created["case_id"], {"X-Case-Token": created["access_token"]}, b""
        )
    assert (res.status_code, res.json()["error"]["code"]) == (422, "document_unreadable")
    assert res.json()["error"]["details"] == {"kind": "passbook"}


async def test_a_png_bomb_is_refused_before_it_is_decoded() -> None:
    async with app_client() as (_, client):
        created = await create_case(client)
        headers = {"X-Case-Token": created["access_token"]}
        huge = await _upload(client, created["case_id"], headers, _png(40_000, 40_000))
        small = await _upload(client, created["case_id"], headers, _png(400, 400))
    assert (huge.status_code, huge.json()["error"]["code"]) == (422, "document_unreadable")
    assert small.status_code == 200


async def test_a_file_too_large_for_the_setting_is_refused() -> None:
    async with app_client(max_upload_mb=1) as (_, client):
        created = await create_case(client)
        res = await _upload(
            client,
            created["case_id"],
            {"X-Case-Token": created["access_token"]},
            _png(10, 10, b"\x00" * (2 * 1024 * 1024)),
        )
    assert (res.status_code, res.json()["error"]["code"]) == (413, "file_too_large")


async def test_uploaded_bytes_are_never_kept() -> None:
    async with app_client() as (container, client):
        created = await create_case(client)
        headers = {"X-Case-Token": created["access_token"]}
        res = await _upload(client, created["case_id"], headers, b"\xff\xd8" + MARKER, "image/jpeg")
        assert res.status_code == 200
        document = res.json()["documents"][-1]
        record = await container.cases.get(created["case_id"])
    assert set(document) == {"id", "kind", "status", "confidence", "fields"}
    assert MARKER.decode() not in res.text
    assert record is not None
    assert MARKER.decode() not in record.view.model_dump_json()


class _LeakyExtractor:
    """Stands in for an OCR pass that read a full number off the page."""

    def ready(self) -> bool:
        return True

    async def extract(
        self, content: bytes, content_type: str, kind: DocumentKind
    ) -> ExtractionResult:
        return ExtractionResult(
            GenericFields(notes="aadhaar 1234 5678 9012, card 6073 9212 3456 4417"), 0.5
        )


async def test_extracted_numbers_are_masked_before_they_are_stored() -> None:
    async with app_client(_extractor=_LeakyExtractor()) as (_, client):
        created = await create_case(client)
        res = await _upload(
            client,
            created["case_id"],
            {"X-Case-Token": created["access_token"]},
            _png(10, 10),
            kind="fir",
        )
    assert res.status_code == 200
    notes = res.json()["documents"][-1]["fields"]["notes"]
    assert notes == "aadhaar XXXX-XXXX-9012, card 6073 92XX XXXX 4417"


async def test_a_typed_aadhaar_is_masked_on_the_way_in() -> None:
    async with app_client() as (_, client):
        created = await create_case(client)
        headers = {"X-Case-Token": created["access_token"]}
        uploaded = await _upload(client, created["case_id"], headers, _png(10, 10), kind="fir")
        document_id = uploaded.json()["documents"][-1]["id"]
        res = await client.patch(
            f"/cases/{created['case_id']}/documents/{document_id}",
            headers=headers,
            json={"fields": {"notes": "her aadhaar is 9999 8888 7777"}},
        )
    assert res.json()["documents"][-1]["fields"]["notes"] == "her aadhaar is XXXX-XXXX-7777"


async def test_an_aadhaar_number_cannot_be_stored_whole() -> None:
    async with app_client() as (_, client):
        created = await create_case(client)
        headers = {"X-Case-Token": created["access_token"]}
        uploaded = await _upload(
            client, created["case_id"], headers, _png(10, 10), kind="aadhaar_deceased"
        )
        document_id = uploaded.json()["documents"][-1]["id"]
        res = await client.patch(
            f"/cases/{created['case_id']}/documents/{document_id}",
            headers=headers,
            json={"fields": {"aadhaar_masked": "1234 5678 9012"}},
        )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"
