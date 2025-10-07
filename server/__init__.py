"""Backend server package for Corrector.

This package contains a minimal FastAPI scaffolding and an in-memory scheduler
to enforce per-plan concurrency and fair-share scheduling. It is designed to
work without external services at first, and be swappable to Postgres/Redis/Celery.

Note: FastAPI/SQLAlchemy are not added as hard dependencies in pyproject yet.
"""

