"""Bilingual "fix before submitting" lines for the blocker flags a PDF prints."""

from app.domain.models import DocumentKind
from app.schemas.evaluation import Flag
from app.services.forms.labels import DOCUMENT_NAMES


def _doc_names(kinds: list[str], index: int) -> str:
    return ", ".join(DOCUMENT_NAMES[DocumentKind(k)][index] for k in kinds)


def _doc_name(kind: str, index: int) -> str:
    return DOCUMENT_NAMES[DocumentKind(kind)][index].split(" (")[0]


def describe(flag: Flag) -> tuple[str, str]:
    """(English, Hindi) text for one blocker flag."""
    p = flag.params
    match flag.code:
        case "name_mismatch":
            (doc_a, doc_b), (name_a, name_b) = p["documents"], p["values"]
            return (
                f'The name is "{name_a}" on the {_doc_name(doc_a, 0).lower()} but "{name_b}" '
                f"on the {_doc_name(doc_b, 0).lower()}. Get it corrected, or ask the branch which "
                "proof of identity it accepts.",
                f'{_doc_name(doc_a, 1)} में नाम "{name_a}" है, '
                f'पर {_doc_name(doc_b, 1)} में "{name_b}" लिखा है। '
                "इसे ठीक करवाएँ, या शाखा से पूछें कि पहचान का कौन-सा प्रमाण चलेगा।",
            )
        case "accident_docs_missing":
            missing = list(p["missing"])
            return (
                f"Accident claims need: {_doc_names(missing, 0)}.",
                f"दुर्घटना के दावे के लिए ज़रूरी: {_doc_names(missing, 1)}।",
            )
        case "nominee_missing":
            return (
                "No nominee is registered. The bank will ask for a legal-heir certificate.",
                "कोई नॉमिनी दर्ज नहीं है। बैंक कानूनी वारिस प्रमाण पत्र माँगेगा।",
            )
        case "account_mismatch":
            accounts = ", ".join(f"XXXX{a}" for a in p["accounts"])
            return (
                f"Passbooks for different accounts were given ({accounts}). Use the account the "
                "premium was debited from.",
                f"अलग-अलग खातों की पासबुक दी गई हैं ({accounts})। वही खाता दें जिससे प्रीमियम कटा था।",
            )
    return flag.message, flag.message
