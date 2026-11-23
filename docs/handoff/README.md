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
