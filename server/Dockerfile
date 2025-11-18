# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project to install the package (corrector) and server deps
COPY pyproject.toml /app/
COPY corrector /app/corrector
COPY settings.py /app/settings.py
COPY server/requirements.txt /app/server/requirements.txt

RUN pip install -e . && pip install -r server/requirements.txt

# Copy server code
COPY server /app/server

EXPOSE 8000

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]

