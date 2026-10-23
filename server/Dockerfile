# Build from the repository root: docker build -f server/Dockerfile .
FROM ghcr.io/astral-sh/uv:0.13.5 AS uv
FROM python:3.11.17-slim-bookworm
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock README.md settings.py ./
COPY corrector/ ./corrector/
COPY server/ ./server/
COPY docs/ ./docs/
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
