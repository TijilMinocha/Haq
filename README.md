# Haq

Poor families are often insured under PMJJBY, PMSBY and RuPay PMJDY without knowing it,
because no policy document is ever issued. Haq treats the bank passbook as the policy
document: photograph it, and Haq finds the covers, checks eligibility with deterministic
rules, cross-checks claim documents, and produces pre-filled claim forms with deadlines.

Built for Hack With Delhi 4.0, Track 1 (claim settlement assistance for micro-insurance).

## Layout

- `server/`: FastAPI + Pydantic v2, managed with uv
- `client/`: React 19 + TypeScript + Vite PWA
- `docs/`: proposal and engineering plan
- `docs/handoff/`: backend-to-frontend handoff (start with `docs/handoff/README.md`)
- `docs/deploy.md`: deploying to Neon, Render and Vercel (free), plus the demo backup

## Run locally

Frontend only, no Docker: see `docs/handoff/frontend-guide.md` section 2
(`STORAGE=memory`, `EXTRACTOR=mock`).

Full stack:

Requires Docker, uv, Node 22 and GNU make (on Windows, run the commands in the
Makefile by hand or use `choco install make`).

```sh
make dev     # postgres + migrations + server :8000 + client :5173
make seed    # demo Bank Mitra accounts (mitra@haq.demo, mitra2@haq.demo)
make test    # includes Postgres integration tests against a haq_test database
make lint
make types   # regenerate client/src/api/schema.d.ts from the server's OpenAPI
```

API docs: http://localhost:8000/docs

## Status

Rules engine (phase 2), Postgres persistence with case code + PIN and Bank Mitra login
(phase 3), Tesseract extraction for passbooks, death certificates, Aadhaar and RuPay
cards (phase 4), and bilingual claim forms and escalation letters (phase 5) are in.
To overlay the official bank forms, see `server/app/infra/pdf/official/README.md`.

Sample document photos for the demo live in `server/app/services/stubs/samples/`
(regenerate with `uv run python -m scripts.make_samples`). OCR tests need the tesseract
binary; without it locally, run the whole suite in Docker:

```sh
docker build --target test -t haq-server-test server && docker run --rm haq-server-test
```

## Privacy

Uploaded images are never stored; only extracted fields are kept, and Aadhaar numbers
are masked to the last four digits at extraction.
