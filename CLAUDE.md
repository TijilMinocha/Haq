# Haq

Finds unclaimed PMJJBY / PMSBY / RuPay PMJDY insurance from a passbook photo
and builds a correct claim. Monorepo: server/ (FastAPI) and client/ (React PWA).
Full plan: docs/haq-plan.pdf.

## Commands
make dev | make test | make lint | make types | make seed

## Architecture
- server: api -> services -> domain (pure) ; infra behind Protocols.
- domain never imports api or infra. Rules are deterministic; no LLM decides eligibility.
- Scheme values live in server/app/domain/config/fy*.yaml, never in code.
- Uploaded files are never stored; only extracted fields. Mask Aadhaar to last 4.
- API contract = Pydantic schemas -> OpenAPI -> client/src/api/schema.d.ts (generated).
  Never edit schema.d.ts by hand; run make types.
- User-facing text is code + params; client translates via i18n.
- Access checks (case token / operator JWT) live only in api/deps.py.
- Zero cost: free tiers and open source only. No paid APIs. OCR is Tesseract;
  speech is the browser Web Speech API. Never send real user documents to a
  free-tier LLM.

## Code style
- Comments only explain why. No what-comments, banners, or commented-out code.
- Docstrings only on non-obvious public functions.
- Fully typed (mypy, TS strict). No any. Small single-purpose files.
- No business logic in routers or React components.
- Every rule and flag code has a unit test.

## Git
- Never run git add, git commit, git push or stage files. Humans do all git writes.
- Read-only git (status, diff, log, branch) is fine.

## Ownership
- server/**, client/src/api, client/src/lib (except speech.ts), client/src/config: backend lead
- client/src/app, components, features, lib/speech.ts, i18n text: Piyush
