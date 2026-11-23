"""Bilingual text printed on the PDFs. The client has its own translations; PDFs are
rendered on the server, so they carry theirs here."""

from app.domain.models import DocumentKind, EventType, Scheme

SCHEME_NAMES: dict[Scheme, tuple[str, str]] = {
    Scheme.PMJJBY: (
        "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "प्रधानमंत्री जीवन ज्योति बीमा योजना",
    ),
    Scheme.PMSBY: ("Pradhan Mantri Suraksha Bima Yojana (PMSBY)", "प्रधानमंत्री सुरक्षा बीमा योजना"),
    Scheme.RUPAY_PMJDY: ("RuPay Card Accident Insurance (PMJDY)", "रुपे कार्ड दुर्घटना बीमा (जन धन)"),
}

EVENT_NAMES: dict[EventType, tuple[str, str]] = {
    EventType.NATURAL_DEATH: ("Death (natural causes)", "मृत्यु (प्राकृतिक)"),
    EventType.ACCIDENTAL_DEATH: ("Death in an accident", "दुर्घटना में मृत्यु"),
    EventType.ACCIDENTAL_DISABILITY: ("Disability from an accident", "दुर्घटना से विकलांगता"),
}

DOCUMENT_NAMES: dict[DocumentKind, tuple[str, str]] = {
    DocumentKind.PASSBOOK: ("Bank passbook (copy)", "बैंक पासबुक (कॉपी)"),
    DocumentKind.DEATH_CERTIFICATE: ("Death certificate", "मृत्यु प्रमाण पत्र"),
    DocumentKind.AADHAAR_DECEASED: ("Aadhaar of the insured", "बीमित का आधार"),
    DocumentKind.AADHAAR_NOMINEE: ("Aadhaar of the nominee", "नॉमिनी का आधार"),
    DocumentKind.FIR: ("FIR (police report)", "FIR (पुलिस रिपोर्ट)"),
    DocumentKind.POSTMORTEM: ("Post-mortem report", "पोस्टमार्टम रिपोर्ट"),
    DocumentKind.DISABILITY_CERTIFICATE: ("Disability certificate", "विकलांगता प्रमाण पत्र"),
    DocumentKind.NOMINEE_BANK_PROOF: (
        "Nominee's bank details (cancelled cheque or passbook)",
        "नॉमिनी का बैंक विवरण (कैंसिल चेक या पासबुक)",
    ),
    DocumentKind.RUPAY_CARD: ("RuPay card (copy)", "रुपे कार्ड (कॉपी)"),
}

RELATIONS_HI: dict[str, str] = {
    "wife": "पत्नी",
    "husband": "पति",
    "son": "पुत्र",
    "daughter": "पुत्री",
    "mother": "माता",
    "father": "पिता",
    "brother": "भाई",
    "sister": "बहन",
}
