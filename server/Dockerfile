FROM python:3.12-slim AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-hin tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /srv
# Render's free instance has 512 MB and a fraction of a CPU: one thread per maths/OCR
# library avoids per-thread buffers that would not fit, and gains nothing on that CPU.
ENV UV_PROJECT_ENVIRONMENT=/srv/.venv \
    PATH="/srv/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OPENBLAS_NUM_THREADS=1 \
    OMP_THREAD_LIMIT=1 \
    MALLOC_ARENA_MAX=2
COPY pyproject.toml uv.lock ./

# Runs the whole suite, including the OCR tests that need the tesseract binary.
FROM base AS test
RUN uv sync --frozen
COPY . .
CMD ["pytest", "-q"]

FROM base AS prod
RUN uv sync --frozen --no-dev
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
RUN useradd --system --uid 10001 haq
USER haq
ENV ENV=prod LOG_JSON=true
EXPOSE 8000
# --proxy-headers: Render's proxy sets X-Forwarded-For, which rate limiting keys on.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --timeout-keep-alive 30"]
