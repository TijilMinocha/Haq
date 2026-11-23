from app.services.forms.data import FormData


def official_values(f: FormData) -> dict[str, str | None]:
    """The values an official form map can place. Keys are what `<SCHEME>.yaml` refers to."""
    return {
        "insured_name": f.insured_name,
        "insured_dob": f.insured_dob,
        "account": f.account,
        "bank": f.bank,
        "branch": f.branch,
        "ifsc": f.ifsc,
        "card": f.card,
        "event": f.event.en if f.event else None,
        "event_date": f.event_date,
        "place": f.place,
        "death_registration": f.death_registration,
        "fir_number": f.fir_number,
        "postmortem_number": f.postmortem_number,
        "claimant_name": f.claimant_name,
        "claimant_relation": f.claimant_relation.en if f.claimant_relation else None,
        "claim_amount": f.claim_amount,
        "prepared_on": f.prepared_on,
        "case_code": f.case_code,
    }
