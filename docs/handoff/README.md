# Handoff: backend → frontend

**From:** Tijil (backend lead) **To:** Piyush (frontend) **Date:** 23 Nov 2026

The backend is further along than "handoff v0" in the plan: every endpoint is live with
the final contract **and** real behaviour (rules engine, Postgres, logins, OCR). Only the
claim-form PDFs are still placeholders. Build every screen against the real server.

## Read in this order

| # | File | What it gives you |
|---|---|---|
| 1 | [CLAUDE-START-HERE.md](CLAUDE-START-HERE.md) | Instructions and the starter prompt for your Claude Code session |
| 2 | [frontend-guide.md](frontend-guide.md) | Status, how to run, the API rules, screens, UX rules, done-when |
| 3 | [api-codes.md](api-codes.md) | Every reason, flag, alert and error code with its params, and phase 4 notes |
| 4 | [demo.md](demo.md) | Demo scenarios, sample photos, test logins and PINs |
| 5 | [../haq-plan.pdf](../haq-plan.pdf) | The full plan. Your sections: 1-5, 7, 8, 9 |
| 6 | [../../CLAUDE.md](../../CLAUDE.md) | Repo rules both Claude sessions follow |
| 7 | `client/src/api/schema.d.ts` | Generated API types. Source of truth for every request and response |
| 8 | http://localhost:8000/docs | Live Swagger docs once the server runs |

## The short version

- Run the server **without Docker**: `STORAGE=memory` and `EXTRACTOR=mock` in
  `server/.env` (see frontend-guide.md).
- `client/src/api`, `client/src/lib` (except `speech.ts`), `client/src/config` and
  `client/src/i18n/index.ts` are already built. Use them; don't rewrite them.
- You own `client/src/app`, `components`, `features`, `lib/speech.ts` and the i18n **text**
  in `en.json` / `hi.json`.
- Ten new reason codes need Hindi and English text. They are listed in api-codes.md.
- Need a new field or endpoint? Ask Tijil. Never edit `schema.d.ts` by hand.

## Handoff v1 (phase 7)

Same API contract, plus production behaviour. What changes for the client:

- **Deployed setup**: see `docs/deploy.md`. Vercel needs `VITE_API_BASE_URL` set to the
  Render URL plus `/api/v1`.
- **Cold start**: the free server sleeps after 15 minutes. The first request can take about
  a minute, so the "waking up" state after 5 seconds (`env.slowRequestMs`) matters.
- **Rate limits**: too many uploads or logins from one phone return
  `429 too_many_attempts` with `details.minutes = 1` and a `Retry-After` header. The
  existing translation for `errors.too_many_attempts` covers it.
- **500 errors** now return `error.code = "internal_error"` with `details.request_id`.
  Add an `errors.internal_error` translation, and show the request id small on the error
  screen so it can be reported. `unknown_error` remains the fallback.
- **Every response** has an `X-Request-ID` header (exposed through CORS).
- **New endpoint** `GET /api/v1/health/ready` reports whether the database and OCR are up.
  It's for monitoring; the app does not need it. Run `npm run types` after pulling.
- **Same-origin API** for the laptop + tunnel backup: with `VITE_API_BASE_URL=/api/v1`,
  `npm run dev` and `npm run preview` forward `/api` to `localhost:8000`.
- **Demo Bank Mitra password** on the deployed server is set by Tijil in Render, and is not
  `haq-demo-2026`. Ask him for it. Locally it is unchanged.
