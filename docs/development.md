# Development

## Layout

- `server/`: FastAPI + Pydantic v2, managed with uv
- `client/`: React 19 + TypeScript + Vite PWA
- `docs/`: proposal, engineering plan, deployment guide
- `docs/handoff/`: backend-to-frontend handoff (start with `docs/handoff/README.md`)

## Run locally

**Frontend only, no Docker:** set `STORAGE=memory` and `EXTRACTOR=mock` in `server/.env`
(see `docs/handoff/frontend-guide.md`, section 2).

**Full stack** needs Docker, uv, Node 22 and GNU make (on Windows, run the Makefile's
commands by hand or `choco install make`):

```sh
make dev     # postgres + migrations + server :8000 + client :5173
make seed    # demo Bank Mitra accounts (mitra@haq.demo, mitra2@haq.demo)
make test    # includes Postgres integration tests against a haq_test database
make lint
make types   # regenerate client/src/api/schema.d.ts from the server's OpenAPI
```

API docs: http://localhost:8000/docs

## OCR and sample documents

Synthetic sample photos live in `server/app/services/stubs/samples/` (regenerate with
`uv run python -m scripts.make_samples`). OCR tests need the tesseract binary; without it
locally, run the whole suite in Docker:

```sh
docker build --target test -t haq-server-test server && docker run --rm haq-server-test
```

On machines low on memory, set `OPENBLAS_NUM_THREADS=1` before running tests.

## Official claim forms

The filled official forms and their field maps live in `server/app/infra/pdf/official/`.
See the README there for how to update a form for a new financial year.

## Deploying

See `docs/deploy.md` (Neon, Render and Vercel, all on free tiers), including the laptop +
Cloudflare tunnel backup for demo day.
