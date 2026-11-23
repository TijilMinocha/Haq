from app.services.forms.data import FormData


def _proof_of_death(f: FormData) -> str | None:
    if not f.is_death or not f.has_death_certificate:
        return None
    if f.death_registration:
        return f"Death certificate, reg. no. {f.death_registration}"
    return "Death certificate"


def official_values(f: FormData) -> dict[str, str | None]:
    """Every value an official form map can place, by the key its `<SCHEME>.yaml` uses.

    Official forms are filled in English: they go to bank staff and the insurer. Names keep
    the script they were written in.
    """
    return {
        "insured_name": f.insured_name,
        "insured_dob": f.insured_dob,
        "bank": f.bank,
        "branch": f.branch,
        "ifsc": f.ifsc,
        "card": f.card,
        "event": f.event.en if f.event else None,
        "event_date": f.event_date,
        "event_day_date": f"{f.event_weekday}, {f.event_date}" if f.event_weekday else None,
        "death_date": f.event_date if f.is_death else None,
        "cause": f.cause,
        "proof_of_death": _proof_of_death(f),
        "place": f.place,
        "death_registration": f.death_registration,
        "fir_number": f.fir_number,
        "postmortem_number": f.postmortem_number,
        "nominee_name": f.claimant_name if f.is_death else None,
        "claimant_name": f.claimant_name,
        "claimant_relation": f.claimant_relation.en if f.claimant_relation else None,
        "claim_amount": f.claim_amount,
        "prepared_on": f.prepared_on,
        "case_code": f.case_code,
    }
