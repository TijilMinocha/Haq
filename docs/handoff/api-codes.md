# API codes (rules engine and extraction)

The API contract did not change in phase 2. The engine now computes every evaluation
instead of replaying fixtures, and it sends these codes. Translate with
`t('reasons.' + code, params)`, `t('flags.' + code, params)` and `t(alert.code, alert.params)`.

## Reason codes (`covers[].reasons[]`)

Already in `en.json` / `hi.json`:

| Code | Params |
| --- | --- |
| premium_debited_current_year | none |
| accidental_event | none |
| card_txn_within_lookback | claim: `days_before_event`; protect: `expires_on`, `days_left` |
| new_card_amount | none |
| death_within_lien_period | `days_since_enrolment`, `lien_days` |
| no_premium_found | none |
| accident_only_cover | none |
| no_premium_this_cover_year | `last_debit` (ISO date) |

New, need text in both locales:

| Code | Params | Meaning |
| --- | --- | --- |
| life_cover_death_only | none | PMJJBY pays only on death, not disability |
| age_above_limit | `max_age` | Insured was past the scheme's age limit |
| disability_extent_needed | `total`, `partial` (rupees) | PMSBY pays `total` or `partial` depending on the disability certificate |
| event_details_missing | none | Fill in what happened and when to confirm this cover |
| no_rupay_card | none | No RuPay card found on this account |
| card_not_eligible | `card_bin` | Card is not a RuPay PMJDY card |
| no_card_txn_in_window | optional `lookback_days` or `last_card_use` | Card not used in the 90 days before |
| only_unverifiable_txns | `lookback_days` | Only UPI/AEPS use seen; the bank must confirm card use |
| old_card_amount | none | Card issued on or before 28 Aug 2018: ₹1 lakh cover |
| card_issue_date_unknown | none | Card issue date unknown; ₹1 lakh assumed until the bank confirms |

## Flag params

| Code | Params |
| --- | --- |
| name_mismatch | `documents` (two DocumentKind values), `values` (the two names) |
| dob_mismatch | `documents`, `values` (ISO dates) |
| account_mismatch | `accounts` (last-4 digits) |
| nominee_missing | none |
| death_within_lien_period | `days_since_enrolment`, `lien_days` |
| rupay_no_recent_txn | `lookback_days` |
| rupay_txn_unverifiable | `lookback_days` |
| accident_docs_missing | `missing` (DocumentKind values) |
| claim_window_closing | `scheme`, `deadline`, `due_date`, `days_left` |
| claim_window_passed | `scheme`, `deadline`, `due_date`, `days_late` |
| ocr_low_confidence | `document_id`, `document` (DocumentKind) |

## Alert params (protect mode)

| Code | Params |
| --- | --- |
| alert.cover_lapsed | `scheme` on the alert; params `last_debit` or `last_card_use` when known |
| alert.rupay_expiring | `days_left`, `expires_on` |
| alert.nominee_missing | none |
| alert.cover_active | `scheme` on the alert |

Alerts arrive ordered: problems first, `alert.cover_active` last.

## Behaviour notes

- Statuses `eligible`, `likely_eligible` and `needs_verification` all count toward
  `total_claimable` in claim mode. Protect mode always has `total_claimable = 0`.
- RuPay in claim mode is never plain `eligible`: the bank must confirm the card was active.
- Demo scenarios shift their dates so the story is the same on any demo day.

# Phase 4: extraction (handoff for the client)

`make types` has been run; `schema.d.ts` now includes `CardFields`.

- **New fields type `CardFields`** for `kind: "rupay_card"`: `card_bin`, `card_last4`,
  `valid_from`, `name`. The full card number is never returned or stored.
- **Uploads now really read the photo.** Expect 2-10 seconds on the free server.
  - `422 document_unreadable` (`details.kind`): show the retake prompt with photo tips.
  - `503 extractor_unavailable`: show a retry button.
- `confidence` is now meaningful (0-1). Below 0.6, the case gets an `ocr_low_confidence`
  flag for that document until the user corrects its fields with PATCH.
- Aadhaar numbers come back as `XXXX-XXXX-1234`, including inside any field the user types.
- **Demo photos** that always extract correctly live in
  `server/app/services/stubs/samples/*.png` (Sunita's passbook, death certificate and RuPay
  card; Meena's passbook; Raju's passbook and card). Uploading Sunita's three photos to a new
  claim case gives ₹6,00,000 with the name-mismatch blocker.
