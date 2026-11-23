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

## Run locally

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

Rules engine (phase 2) and Postgres persistence with case code + PIN and Bank Mitra
login (phase 3) are in. Document extraction still returns empty fields (phase 4).

## Privacy

Uploaded images are never stored; only extracted fields are kept, and Aadhaar numbers
are masked to the last four digits at extraction.
