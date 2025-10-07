# Multi-stage build for corrector server
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for layer caching)
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY corrector/ ./corrector/
COPY server/ ./server/
COPY settings.py ./
COPY docs/ ./docs/

# Create outputs directory
RUN mkdir -p outputs /data

# Default runtime env
ENV LOG_LEVEL=info \
    SYSTEM_MAX_WORKERS=2 \
    DEMO_PLAN=free \
    STORAGE_DIR=/data

# Non-root user for security
RUN useradd -m -u 1000 corrector && \
    chown -R corrector:corrector /app /data
USER corrector

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
