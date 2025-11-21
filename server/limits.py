from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanLimits:
    name: str
    max_runs_concurrent: int
    max_docs_per_run: int
    max_docs_concurrent: int
    rate_limit_rpm: int
    ai_enabled: bool


FREE = PlanLimits(
    name="free",
    max_runs_concurrent=1,
    max_docs_per_run=1,
    max_docs_concurrent=1,
    rate_limit_rpm=60,
    ai_enabled=True,
)

PREMIUM = PlanLimits(
    name="premium",
    max_runs_concurrent=2,
    max_docs_per_run=3,
    max_docs_concurrent=3,
    rate_limit_rpm=300,
    ai_enabled=True,
)

# System-wide default workers for local single-node deployment
SYSTEM_MAX_WORKERS = 2
