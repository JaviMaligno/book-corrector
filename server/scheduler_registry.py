from __future__ import annotations

import os

from .limits import SYSTEM_MAX_WORKERS
from .scheduler import InMemoryScheduler

_scheduler: InMemoryScheduler | None = None


def get_scheduler() -> InMemoryScheduler:
    global _scheduler
    if _scheduler is None:
        sys_workers = int(os.environ.get("SYSTEM_MAX_WORKERS", str(SYSTEM_MAX_WORKERS)))
        _scheduler = InMemoryScheduler(system_max_workers=sys_workers)
    return _scheduler

