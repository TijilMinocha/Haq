from httpx import AsyncClient


async def _demo(client: AsyncClient, scenario: str) -> tuple[str, dict[str, str]]:
    res = await client.post(f"/demo/scenarios/{scenario}")
    assert res.status_code == 201
    body = res.json()
    return body["case_id"], {"X-Case-Token": body["access_token"]}


async def test_scenarios_listed(client: AsyncClient) -> None:
    res = await client.get("/demo/scenarios")
    assert {s["id"] for s in res.json()} == {"sunita_accident", "meena_lien", "raju_protect"}


async def test_sunita_totals_six_lakh_with_name_blocker(client: AsyncClient) -> None:
    case_id, headers = await _demo(client, "sunita_accident")
    evaluation = (await client.get(f"/cases/{case_id}", headers=headers)).json()["evaluation"]
    assert evaluation["total_claimable"] == 600000
    assert {"name_mismatch", "accident_docs_missing"} <= {f["code"] for f in evaluation["flags"]}
    assert all(isinstance(d["days_left"], int) for d in evaluation["deadlines"])


async def test_meena_pmjjby_ineligible(client: AsyncClient) -> None:
    case_id, headers = await _demo(client, "meena_lien")
    covers = (await client.get(f"/cases/{case_id}", headers=headers)).json()["evaluation"]["covers"]
    pmjjby = next(c for c in covers if c["scheme"] == "PMJJBY")
    assert pmjjby["status"] == "ineligible"
    assert pmjjby["reasons"][0]["code"] == "death_within_lien_period"


async def test_raju_alerts(client: AsyncClient) -> None:
    case_id, headers = await _demo(client, "raju_protect")
    alerts = (await client.get(f"/cases/{case_id}", headers=headers)).json()["evaluation"]["alerts"]
    assert {"alert.cover_lapsed", "alert.rupay_expiring", "alert.nominee_missing"} <= {
        a["code"] for a in alerts
    }


async def test_unknown_scenario(client: AsyncClient) -> None:
    res = await client.post("/demo/scenarios/nope")
    assert res.status_code == 404


async def test_upload_correct_delete_document(client: AsyncClient) -> None:
    case_id, headers = await _demo(client, "sunita_accident")
    res = await client.post(
        f"/cases/{case_id}/documents",
        headers=headers,
        data={"kind": "fir"},
        files={"file": ("fir.jpg", b"\xff\xd8fake", "image/jpeg")},
    )
    assert res.status_code == 200
    doc = next(d for d in res.json()["documents"] if d["kind"] == "fir")

    res = await client.patch(
        f"/cases/{case_id}/documents/{doc['id']}",
        headers=headers,
        json={"fields": {"reference_number": "FIR-118/2026"}},
    )
    fixed = next(d for d in res.json()["documents"] if d["id"] == doc["id"])
    assert fixed["status"] == "corrected"
    assert fixed["fields"]["reference_number"] == "FIR-118/2026"

    res = await client.delete(f"/cases/{case_id}/documents/{doc['id']}", headers=headers)
    assert all(d["id"] != doc["id"] for d in res.json()["documents"])


async def test_upload_rejects_wrong_type(client: AsyncClient) -> None:
    case_id, headers = await _demo(client, "sunita_accident")
    res = await client.post(
        f"/cases/{case_id}/documents",
        headers=headers,
        data={"kind": "fir"},
        files={"file": ("x.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 415
    assert res.json()["error"]["code"] == "unsupported_file"


async def test_form_pdf_and_not_applicable(client: AsyncClient) -> None:
    case_id, headers = await _demo(client, "sunita_accident")
    res = await client.get(f"/cases/{case_id}/forms/PMJJBY", headers=headers)
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF")

    meena_id, meena_headers = await _demo(client, "meena_lien")
    res = await client.get(f"/cases/{meena_id}/forms/PMJJBY", headers=meena_headers)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "form_not_applicable"


async def test_escalation_letter(client: AsyncClient) -> None:
    case_id, headers = await _demo(client, "sunita_accident")
    res = await client.get(
        f"/cases/{case_id}/letters/escalation", params={"scheme": "PMSBY"}, headers=headers
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
