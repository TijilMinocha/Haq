from httpx import AsyncClient

from app.services.auth_service import SEED_OPERATORS


async def _create(client: AsyncClient, pin: str = "4321") -> dict[str, str]:
    res = await client.post("/cases", json={"mode": "claim", "language": "hi", "pin": pin})
    assert res.status_code == 201
    body: dict[str, str] = res.json()
    return body


async def _operator_token(client: AsyncClient) -> str:
    email, _, password = SEED_OPERATORS[0]
    res = await client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    token: str = res.json()["access_token"]
    return token


async def test_health(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.json() == {"status": "ok"}


async def test_schemes_come_from_config(client: AsyncClient) -> None:
    res = await client.get("/meta/schemes")
    amounts = {s["scheme"]: s["max_amount"] for s in res.json()}
    assert amounts == {"PMJJBY": 200000, "PMSBY": 200000, "RUPAY_PMJDY": 200000}


async def test_create_then_read_with_case_token(client: AsyncClient) -> None:
    created = await _create(client)
    assert created["case_code"].startswith("HAQ-")
    res = await client.get(
        f"/cases/{created['case_id']}", headers={"X-Case-Token": created["access_token"]}
    )
    assert res.status_code == 200
    assert res.json()["mode"] == "claim"


async def test_case_requires_token(client: AsyncClient) -> None:
    created = await _create(client)
    res = await client.get(f"/cases/{created['case_id']}")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_token"


async def test_resume_with_code_and_pin(client: AsyncClient) -> None:
    created = await _create(client, pin="9876")
    res = await client.post(
        "/cases/resume", json={"case_code": created["case_code"], "pin": "9876"}
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    view = await client.get(f"/cases/{created['case_id']}", headers={"X-Case-Token": token})
    assert view.status_code == 200


async def test_wrong_pin_locks_after_five_attempts(client: AsyncClient) -> None:
    created = await _create(client, pin="1111")
    body = {"case_code": created["case_code"], "pin": "0000"}
    for _ in range(5):
        assert (await client.post("/cases/resume", json=body)).status_code == 401
    res = await client.post("/cases/resume", json={**body, "pin": "1111"})
    assert res.status_code == 429
    assert res.json()["error"]["code"] == "too_many_attempts"


async def test_patch_merges_nested_fields(client: AsyncClient) -> None:
    created = await _create(client)
    headers = {"X-Case-Token": created["access_token"]}
    url = f"/cases/{created['case_id']}"
    await client.patch(url, json={"subject": {"name": "Ramesh Kumar"}}, headers=headers)
    res = await client.patch(
        url, json={"subject": {"date_of_birth": "1984-03-12"}}, headers=headers
    )
    assert res.json()["subject"] == {"name": "Ramesh Kumar", "date_of_birth": "1984-03-12"}


async def test_operator_owns_cases_they_create(client: AsyncClient) -> None:
    token = await _operator_token(client)
    auth = {"Authorization": f"Bearer {token}"}
    res = await client.post("/cases", json={"mode": "claim", "pin": "1234"}, headers=auth)
    case_id = res.json()["case_id"]
    assert (await client.get(f"/cases/{case_id}", headers=auth)).status_code == 200
    listed = await client.get("/operator/cases", headers=auth)
    assert [c["id"] for c in listed.json()] == [case_id]


async def test_operator_cannot_open_other_case(client: AsyncClient) -> None:
    created = await _create(client)
    token = await _operator_token(client)
    res = await client.get(
        f"/cases/{created['case_id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "forbidden"


async def test_bad_login(client: AsyncClient) -> None:
    res = await client.post("/auth/login", json={"email": "x@y.z", "password": "nope"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"


async def test_validation_error_shape(client: AsyncClient) -> None:
    res = await client.post("/cases", json={"mode": "claim", "pin": "12"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"
