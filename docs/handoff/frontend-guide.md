# Frontend guide

Covers plan sections 7 and 8 with what has changed since the plan was written.

## 1. Backend status

| Area | Status |
|---|---|
| API contract (all endpoints in plan section 5.2) | Final. Live at `/docs` |
| Rules engine (PMJJBY, PMSBY, RuPay, cross-checks, deadlines, alerts) | Real |
| Persistence (Postgres), case code + PIN, Bank Mitra login, lockout | Real |
| Document reading (Tesseract OCR, Aadhaar masking) | Real. `EXTRACTOR=mock` for dev |
| Claim forms and escalation letter PDFs | Real. Official claim form filled in (PMJJBY, PMSBY, RuPay 2026-27), then Haq's bilingual details pages; Hindi + English letter (family's language first) |
| Deployed URL | Not yet (phase 7). Use localhost |

Differences from the plan text:

- New `CardFields` type for `kind: "rupay_card"` uploads.
- Ten reason codes not in the plan. They need translations; see api-codes.md.
- RuPay in claim mode is `likely_eligible`, never plain `eligible`.

## 2. Run it locally (no Docker needed)

Needs: Node 22, and [uv](https://docs.astral.sh/uv/) for Python
(`powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` on Windows).

Server, in one terminal:

```powershell
cd server
Copy-Item .env.example .env
```

Edit `server/.env` and set these two lines (everything else can stay):

```
STORAGE=memory
EXTRACTOR=mock
```

```powershell
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

- `STORAGE=memory`: no database needed. Data resets when the server restarts.
- `EXTRACTOR=mock`: no Tesseract needed. The sample photos in
  `server/app/services/stubs/samples/` return real fields. Any other image returns empty
  fields that the user corrects by hand.

Client, in a second terminal:

```powershell
cd client
Copy-Item .env.example .env
npm install
npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.

After Tijil changes the API, pull and run `npm run types` in `client/`, or `make types`
if you have make. Both regenerate `src/api/schema.d.ts`.

## 3. Already built for you (don't rewrite)

| File | What it gives you |
|---|---|
| `src/api/schema.d.ts` | Generated types for every request and response |
| `src/api/types.ts` | Short names: `CaseView`, `Flag`, `CoverResult`, `Alert`, ... |
| `src/api/client.ts` | Typed fetch client. Adds `X-Case-Token` or the operator's Bearer token automatically. Logs the operator out on a 401 |
| `src/api/errors.ts` | `ApiError { code, message, status, details }` and `isApiError(e, code)` |
| `src/api/hooks.ts` | `useCase(id)`, `useCreateCase()`, `useResumeCase()`, `useUpdateCase(id)`, `useUploadDocument(id)`, `useUpdateDocument(id)`, `useDeleteDocument(id)`, `useSchemes()`, `useDemoScenarios()`, `useStartDemo()`, `useLogin()`, `useLogout()`, `useMe()`, `useOperatorCases(filters)` |
| `src/api/downloads.ts` | `downloadForm(caseId, scheme)`, `downloadEscalation(caseId, scheme)` |
| `src/lib/caseStore.ts` | Saves case tokens and codes per case in localStorage |
| `src/lib/authStore.ts` | Operator session, `isOperator()`, `subscribeOperator` for `useSyncExternalStore` |
| `src/lib/format.ts` | `formatINR` (₹6,00,000), `formatDate(iso, lang)`, `daysLeftLabel(days, t)` |
| `src/lib/image.ts` | `compressImage(file)`: max 1600px, JPEG about 0.7. PDFs pass through |
| `src/i18n/index.ts` | i18next setup, Hindi default, `setLanguage(lang)` |
| `src/i18n/locales/*.json` | Keys for every flag, alert, error and the plan's reason codes |

`src/App.tsx` and `src/main.tsx` are placeholders. Replace them with your app shell.

## 4. Rules for using the API

- Mutation hooks write the returned `CaseView` into the `['case', id]` query cache. Don't
  add manual refetches.
- Always `compressImage` before upload. Show a per-document spinner while uploading. OCR
  takes 2-10 seconds on the real server.
- Upload errors:
  - `document_unreadable` (422): show a retake prompt with photo tips.
  - `extractor_unavailable` (503): show a retry button.
  - `unsupported_file` (415) and `file_too_large` (413): explain and offer a retake.
- Never show `message` when a translation exists:
  - flags: `t('flags.' + code, params)`
  - reasons: `t('reasons.' + code, params)`
  - alerts: `t(code, params)` (alert codes already start with `alert.`)
  - errors: `t('errors.' + code, details)`
- `evaluation.total_claimable` is the hero number. Flags arrive already sorted:
  blocker, warning, info.
- `/demo` with `useStartDemo` is the route for live judging (unlinked).
- After a case is created, show the case code large with a "write this down" prompt, and
  ask for the PIN on that screen.
- `too_many_attempts` (429): show the wait (`details.minutes`). `forbidden` (403): send
  operators back to their case list.
- The first request after the free server sleeps can take about a minute. Show a friendly
  "waking up" state if a request passes 5 seconds (`env.slowRequestMs`).

## 5. Screens and routes (plan 8.1)

| Route | Screen | Key data |
|---|---|---|
| `/` | Language picker (Hindi default), then mode: "Claim for a family member", "Check my own cover", "Continue my case" | `useCreateCase` |
| `/resume` | Case code + PIN | `useResumeCase` |
| `/case/:id/created` | Case code large; set PIN | `useCase` |
| `/case/:id/event` | Who, natural or accident, date, nominee; voice input on every field | `useUpdateCase`, `lib/speech.ts` |
| `/case/:id/scan` | Passbook capture (camera first, gallery fallback), preview, retake | `useUploadDocument` |
| `/case/:id/result` | Hero total, a cover card per scheme with evidence lines, top blockers, read-aloud | `useCase`, `lib/speech.ts` |
| `/case/:id/documents` | Checklist per scheme, upload per item, flags inline, edit extracted fields | `useUploadDocument`, `useUpdateDocument` |
| `/case/:id/submit` | Form download per scheme, deadline countdowns, "take these to your bank" steps, escalation letter | `downloads.ts` |
| `/case/:id/alerts` | Protect mode: alerts with one clear action each | `useCase` |
| `/operator/login` | Bank Mitra login | `useLogin` |
| `/operator` | Case list: status filter, search by name or code, "new case" | `useOperatorCases`, `useMe` |
| `/demo` | Scenario picker for judges | `useDemoScenarios`, `useStartDemo` |

Order of work (plan 8.2): app shell → UI kit → landing, case-created, resume → event → scan
→ **result (the demo's hero moment, most polish)** → documents → submit → protect alerts →
voice (`lib/speech.ts`, Web Speech API, `hi-IN`; hide the mic where unsupported) →
operator login and list → PWA → demo route and a low-end Android polish pass.

## 6. UX rules (plan 8.3)

- 360px width first. Tap targets ≥ 48px, body text ≥ 16px.
- Hindi is the default. Every action has an icon and a short word. No insurance jargon;
  explain each scheme in one line (`schemes.<SCHEME>.explanation`).
- One primary action per screen. Always show the current step.
- Big money numbers, Indian grouping (`formatINR`).
- File input: `accept="image/*" capture="environment"`.
- Slow networks: skeletons, upload progress, automatic retry on network errors, no layout
  jumps.
- Never a dead end: every error state has a next action.
- AA contrast, labelled inputs, visible focus, audio for key results.

## 7. Done when (plan 8.4)

- The Sunita scenario runs end to end in under 60 seconds on a phone.
- Every flag, alert, reason and error code shows Hindi and English text.
- Installable PWA, usable with Chrome's low-end mobile throttling.
- ESLint, tsc and Vitest pass in CI.

## 8. Code standards and git (plan section 9)

- Comments explain only *why*. No what-comments, banners or commented-out code.
- No business logic in components; components call hooks.
- Strict TypeScript, no `any`. Small files (aim for under 300 lines).
- UI constants live in one file; no magic numbers.
- `TODO(piyush): ...`. A TODO always names an owner.
- Branches: `piyush/feat/<thing>`, small PRs into `main`, conventional commit messages.
  `main` is protected and needs one review.
- Claude Code never runs `git add`, `commit` or `push`. Humans do all git writes.

## 9. Talking to the backend

- New fields or endpoints: ask Tijil first. He changes the schema and regenerates types.
- If anything behaves differently from this guide or `schema.d.ts`, report it as a
  backend bug.
