from httpx import AsyncClient

from app.services.auth_service import SEED_OPERATORS

from .conftest import AppFactory


async def _login(client: AsyncClient, index: int = 0) -> dict[str, str]:
    email, _, password = SEED_OPERATORS[index]
    res = await client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def test_case_survives_restart_and_resumes_on_second_device(
    app_instance: AppFactory,
) -> None:
    async with app_instance() as phone:
        created = (
            await phone.post("/cases", json={"mode": "claim", "language": "hi", "pin": "2468"})
        ).json()
        headers = {"X-Case-Token": created["access_token"]}
        await phone.patch(
            f"/cases/{created['case_id']}",
            headers=headers,
            json={"subject": {"name": "Ramesh Kumar"}, "event": {"type": "accidental_death"}},
        )

    async with app_instance() as restarted:
        res = await restarted.get(f"/cases/{created['case_id']}", headers=headers)
        assert res.status_code == 200
        assert res.json()["subject"]["name"] == "Ramesh Kumar"
        assert res.json()["event"]["type"] == "accidental_death"

    async with app_instance() as second_phone:
        resumed = await second_phone.post(
            "/cases/resume", json={"case_code": created["case_code"], "pin": "2468"}
        )
        assert resumed.status_code == 200
        token = {"X-Case-Token": resumed.json()["access_token"]}
        assert (await second_phone.get(f"/cases/{created['case_id']}", headers=token)).is_success
        # The first device's token keeps working after the second device resumes.
        assert (await second_phone.get(f"/cases/{created['case_id']}", headers=headers)).is_success


async def test_demo_documents_persist_in_order_and_evaluate(app_instance: AppFactory) -> None:
    async with app_instance() as client:
        started = (await client.post("/demo/scenarios/sunita_accident")).json()
        headers = {"X-Case-Token": started["access_token"]}
        url = f"/cases/{started['case_id']}"
        uploaded = await client.post(
            f"{url}/documents",
            headers=headers,
            data={"kind": "fir"},
            files={"file": ("fir.jpg", b"\xff\xd8fake", "image/jpeg")},
        )
        fir_id = uploaded.json()["documents"][-1]["id"]
        await client.patch(
            f"{url}/documents/{fir_id}",
            headers=headers,
            json={"fields": {"reference_number": "FIR-118/2026"}},
        )

    async with app_instance() as client:
        view = (await client.get(url, headers=headers)).json()
        assert [d["kind"] for d in view["documents"]] == ["passbook", "death_certificate", "fir"]
        fir = view["documents"][2]
        assert (fir["status"], fir["fields"]["reference_number"]) == ("corrected", "FIR-118/2026")
        assert len(view["documents"][0]["fields"]["transactions"]) == 4
        assert view["evaluation"]["total_claimable"] == 600000

        res = await client.delete(f"{url}/documents/{fir_id}", headers=headers)
        assert [d["kind"] for d in res.json()["documents"]] == ["passbook", "death_certificate"]

    async with app_instance() as client:
        view = (await client.get(url, headers=headers)).json()
        assert len(view["documents"]) == 2


async def test_operators_see_only_their_own_cases(app_instance: AppFactory) -> None:
    async with app_instance() as client:
        first, second = await _login(client, 0), await _login(client, 1)
        created = await client.post("/cases", json={"mode": "claim", "pin": "1357"}, headers=first)
        case_id = created.json()["case_id"]

    async with app_instance() as client:
        assert (await client.get(f"/cases/{case_id}", headers=first)).status_code == 200
        res = await client.get(f"/cases/{case_id}", headers=second)
        assert (res.status_code, res.json()["error"]["code"]) == (403, "forbidden")
        mine = await client.get("/operator/cases", headers=first)
        assert [c["id"] for c in mine.json()] == [case_id]
        assert (await client.get("/operator/cases", headers=second)).json() == []


async def test_pin_lockout_holds_across_instances(app_instance: AppFactory) -> None:
    async with app_instance() as client:
        created = (await client.post("/cases", json={"mode": "claim", "pin": "1111"})).json()
    wrong = {"case_code": created["case_code"], "pin": "0000"}
    for _ in range(3):
        async with app_instance() as client:
            assert (await client.post("/cases/resume", json=wrong)).status_code == 401
    async with app_instance() as client:
        for _ in range(2):
            assert (await client.post("/cases/resume", json=wrong)).status_code == 401
    async with app_instance() as client:
        res = await client.post("/cases/resume", json={**wrong, "pin": "1111"})
        assert res.status_code == 429


async def test_login_lockout_and_reset(app_instance: AppFactory) -> None:
    email, _, password = SEED_OPERATORS[0]
    async with app_instance() as client:
        for _ in range(4):
            bad = await client.post("/auth/login", json={"email": email, "password": "nope"})
            assert bad.status_code == 401
        # A success clears the count, so the next mistake does not lock the account.
        assert (
            await client.post("/auth/login", json={"email": email, "password": password})
        ).is_success
        bad = await client.post("/auth/login", json={"email": email, "password": "nope"})
        assert bad.status_code == 401


async def test_seeding_is_idempotent(app_instance: AppFactory) -> None:
    for _ in range(2):
        async with app_instance() as client:
            await _login(client)
