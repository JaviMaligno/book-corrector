FROM ghcr.io/astral-sh/uv:0.13.5 AS uv
FROM python:3.11.17-slim-bookworm AS builder
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock README.md settings.py ./
COPY corrector/ ./corrector/
COPY server/ ./server/
RUN uv sync --frozen --no-dev

FROM python:3.11.17-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY corrector/ ./corrector/
COPY server/ ./server/
COPY settings.py ./
COPY docs/ ./docs/
RUN mkdir -p outputs /data && useradd -m -u 1000 corrector && chown -R corrector:corrector /app /data
ENV PATH="/app/.venv/bin:$PATH" LOG_LEVEL=info SYSTEM_MAX_WORKERS=2 DEMO_PLAN=free STORAGE_DIR=/data
USER corrector
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
