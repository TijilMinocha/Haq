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
make dev     # postgres + server :8000 + client :5173
make test
make lint
make types   # regenerate client/src/api/schema.d.ts from the server's OpenAPI
```

API docs: http://localhost:8000/docs

## Status

Handoff v0: every endpoint returns fixture data from the three demo scenarios with
the final contract. Real extraction, rules and persistence come next.

## Privacy

Uploaded images are never stored; only extracted fields are kept, and Aadhaar numbers
are masked to the last four digits at extraction.
