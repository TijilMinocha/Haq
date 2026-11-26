"""Audit items 1-4: who may touch which case, and which routes ask for credentials at all."""

from typing import Any

import pytest

from app.core.config import Settings
from app.main import create_app

from .conftest import add_document, app_client, create_case, login

# Every route that takes a case id, with a body where the route needs one.
_CASE_ROUTES: tuple[tuple[str, str, dict[str, Any]], ...] = (
    ("GET", "/cases/{case}", {}),
    ("PATCH", "/cases/{case}", {"json": {"subject": {"name": "Someone Else"}}}),
    (
        "POST",
        "/cases/{case}/documents",
        {"data": {"kind": "fir"}, "files": {"file": ("f.jpg", b"\xff\xd8photo", "image/jpeg")}},
    ),
    ("PATCH", "/cases/{case}/documents/{doc}", {"json": {"fields": {"notes": "x"}}}),
    ("DELETE", "/cases/{case}/documents/{doc}", {}),
    ("GET", "/cases/{case}/forms/PMJJBY", {}),
    ("GET", "/cases/{case}/letters/escalation?scheme=PMSBY", {}),
)

# Route -> what stands in front of it. The audit doc repeats this table.
_PUBLIC_ROUTES = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/health/ready"),
    ("GET", "/api/v1/meta/schemes"),
    ("GET", "/api/v1/demo/scenarios"),
    ("POST", "/api/v1/demo/scenarios/{scenario_id}"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/cases"),
    ("POST", "/api/v1/cases/resume"),
}
_GUARDED_ROUTES = {
    ("GET", "/api/v1/auth/me"),
    ("GET", "/api/v1/operator/cases"),
    ("GET", "/api/v1/cases/{case_id}"),
    ("PATCH", "/api/v1/cases/{case_id}"),
    ("POST", "/api/v1/cases/{case_id}/documents"),
    ("PATCH", "/api/v1/cases/{case_id}/documents/{document_id}"),
    ("DELETE", "/api/v1/cases/{case_id}/documents/{document_id}"),
    ("GET", "/api/v1/cases/{case_id}/forms/{scheme}"),
    ("GET", "/api/v1/cases/{case_id}/letters/escalation"),
}


def test_the_route_list_matches_the_documented_guards() -> None:
    # The OpenAPI schema is the published contract, so a new route cannot appear without
    # being classified here as public or guarded.
    paths = create_app(Settings(env="test", storage="memory", extractor="mock")).openapi()["paths"]
    found = {
        (method.upper(), path)
        for path, operations in paths.items()
        for method in operations
        if method.upper() in {"GET", "POST", "PATCH", "PUT", "DELETE"}
    }
    assert found == _PUBLIC_ROUTES | _GUARDED_ROUTES


@pytest.mark.parametrize(("method", "template", "kwargs"), _CASE_ROUTES)
async def test_every_case_route_needs_credentials(
    method: str, template: str, kwargs: dict[str, Any]
) -> None:
    async with app_client() as (_, client):
        created = await create_case(client)
        document_id = await add_document(client, created["case_id"], _token(created))
        url = template.format(case=created["case_id"], doc=document_id)
        res = await client.request(method, url, **kwargs)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_token"


@pytest.mark.parametrize(("method", "template", "kwargs"), _CASE_ROUTES)
async def test_case_token_does_not_open_another_case(
    method: str, template: str, kwargs: dict[str, Any]
) -> None:
    async with app_client() as (_, client):
        mine = await create_case(client, pin="1111")
        theirs = await create_case(client, pin="2222")
        my_document = await add_document(client, mine["case_id"], _token(mine))
        their_document = await add_document(client, theirs["case_id"], _token(theirs))
        url = template.format(case=theirs["case_id"], doc=their_document)
        assert my_document != their_document
        res = await client.request(method, url, headers=_token(mine), **kwargs)
        unchanged = await client.get(f"/cases/{theirs['case_id']}", headers=_token(theirs))
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_token"
    # Nothing leaked and nothing was written.
    assert len(unchanged.json()["documents"]) == 1


@pytest.mark.parametrize(("method", "template", "kwargs"), _CASE_ROUTES)
async def test_operator_cannot_open_a_case_they_do_not_own(
    method: str, template: str, kwargs: dict[str, Any]
) -> None:
    async with app_client() as (_, client):
        owner = {"Authorization": f"Bearer {await login(client, 0)}"}
        other = {"Authorization": f"Bearer {await login(client, 1)}"}
        created_res = await client.post(
            "/cases", json={"mode": "claim", "pin": "1234"}, headers=owner
        )
        created = created_res.json()
        document_id = await add_document(client, created["case_id"], owner)
        url = template.format(case=created["case_id"], doc=document_id)
        res = await client.request(method, url, headers=other, **kwargs)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "forbidden"


async def test_document_id_from_one_case_is_not_found_under_another() -> None:
    async with app_client() as (_, client):
        mine = await create_case(client, pin="1111")
        theirs = await create_case(client, pin="2222")
        my_document = await add_document(client, mine["case_id"], _token(mine))
        url = f"/cases/{theirs['case_id']}/documents/{my_document}"
        patched = await client.patch(url, headers=_token(theirs), json={"fields": {"notes": "x"}})
        deleted = await client.delete(url, headers=_token(theirs))
        still_there = await client.get(f"/cases/{mine['case_id']}", headers=_token(mine))
    assert (patched.status_code, deleted.status_code) == (404, 404)
    assert patched.json()["error"]["code"] == "document_not_found"
    assert [d["id"] for d in still_there.json()["documents"]] == [my_document]


async def test_operator_routes_need_an_operator_token() -> None:
    async with app_client() as (_, client):
        assert (await client.get("/auth/me")).status_code == 401
        assert (await client.get("/operator/cases")).status_code == 401
        garbage = {"Authorization": "Bearer not-a-real-token"}
        assert (await client.get("/auth/me", headers=garbage)).status_code == 401
        assert (await client.get("/operator/cases", headers=garbage)).status_code == 401


async def test_a_bad_bearer_fails_closed_on_a_public_route() -> None:
    async with app_client() as (_, client):
        res = await client.post(
            "/cases",
            json={"mode": "claim", "pin": "1234"},
            headers={"Authorization": "Bearer nonsense"},
        )
    assert (res.status_code, res.json()["error"]["code"]) == (401, "invalid_token")


async def test_operators_only_list_their_own_cases() -> None:
    async with app_client() as (_, client):
        owner = {"Authorization": f"Bearer {await login(client, 0)}"}
        other = {"Authorization": f"Bearer {await login(client, 1)}"}
        mine = (
            await client.post("/cases", json={"mode": "claim", "pin": "1234"}, headers=owner)
        ).json()
        anonymous = await create_case(client, pin="9999")
        their_list = (await client.get("/operator/cases", headers=other)).json()
        my_list = (await client.get("/operator/cases", headers=owner)).json()
    assert their_list == []
    assert [c["id"] for c in my_list] == [mine["case_id"]]
    assert anonymous["case_id"] not in [c["id"] for c in my_list]


async def test_a_case_made_without_an_operator_belongs_to_nobody() -> None:
    async with app_client() as (_, client):
        created = await create_case(client, pin="1234")
        holder = {"Authorization": f"Bearer {await login(client, 0)}"}
        res = await client.get(f"/cases/{created['case_id']}", headers=holder)
    assert (res.status_code, res.json()["error"]["code"]) == (403, "forbidden")


def _token(created: dict[str, str]) -> dict[str, str]:
    return {"X-Case-Token": created["access_token"]}
