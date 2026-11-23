# Demo data

Everything here is invented: names, accounts, card and Aadhaar numbers.

## Seeded scenarios (`/demo` route, `POST /api/v1/demo/scenarios/{id}`)

The scenarios shift their dates so that the story is identical on any day.

| ID | Story | What the screen should show |
|---|---|---|
| `sunita_accident` | Husband Ramesh died in a road accident; she thinks there is no insurance | **₹6,00,000** across PMJJBY + PMSBY + RuPay. Blockers: `name_mismatch` (death certificate says "Rames Kumar") and `accident_docs_missing` (FIR, post-mortem). Deadlines: 22, 22 and 82 days |
| `meena_lien` | Husband died of natural causes 20 days after joining PMJJBY | ₹0. PMJJBY `ineligible` with reason `death_within_lien_period`, plus an info flag |
| `raju_protect` | Living user checks his own cover | Alerts: `alert.cover_lapsed` (PMJJBY), `alert.rupay_expiring` (12 days), `alert.nominee_missing`, `alert.cover_active` (PMSBY) |

PIN for every demo case: **1234**.

## Sample photos (real upload flow)

Folder: `server/app/services/stubs/samples/`. Each `.png` has a `.json` with the exact
fields it produces. They work with `EXTRACTOR=mock` (matched by file content) **and** with
real Tesseract.

| File | Upload as `kind` |
|---|---|
| `sunita_passbook.png` | `passbook` |
| `sunita_death_certificate.png` | `death_certificate` |
| `sunita_rupay_card.png` | `rupay_card` |
| `meena_passbook.png` | `passbook` |
| `raju_passbook.png` | `passbook` |
| `raju_rupay_card.png` | `rupay_card` |

Sunita from scratch: create a claim case, set the event (`accidental_death`, 2026-11-15),
subject "Ramesh Kumar" and nominee "Sunita Devi". Then upload her three photos. The total
reaches ₹6,00,000 once the RuPay card is in. With only the passbook it is ₹5,00,000,
because RuPay assumes the ₹1 lakh old-card amount until the card's issue date is known.

## Bank Mitra test logins

Seeded on every server start. There is no public sign-up.

| Email | Password |
|---|---|
| `mitra@haq.demo` | `haq-demo-2026` |
| `mitra2@haq.demo` | `haq-demo-2026` |

Use the second account to show that one Bank Mitra cannot open another's case (403).
