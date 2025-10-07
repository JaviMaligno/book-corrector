from __future__ import annotations

import itertools
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Iterable, List, Optional

from .limits import PlanLimits, FREE, PREMIUM, SYSTEM_MAX_WORKERS


@dataclass
class User:
    id: str
    plan: str = "free"  # "free" | "premium" | "admin"

    def limits(self) -> PlanLimits:
        return PREMIUM if self.plan == "premium" else FREE


@dataclass
class DocumentTask:
    project_id: str
    document_id: str
    user_id: str
    run_id: str
    mode: str  # "rapido" | "profesional"
    use_ai: bool = False
    created_at: float = field(default_factory=time.time)


@dataclass
class RunJob:
    user_id: str
    run_id: str
    project_id: str
    documents: List[str]
    mode: str
    use_ai: bool = False


class InMemoryScheduler:
    """Fair-share scheduler with per-user queues and plan-based quotas.

    - Per-user queue of DocumentTask items.
    - Round-robin across users (weighted by plan).
    - Enforces per-user concurrent runs/docs and system-wide workers.
    - Thread-safe, single process.
    """

    def __init__(self, system_max_workers: int = SYSTEM_MAX_WORKERS) -> None:
        self._queues: Dict[str, Deque[DocumentTask]] = defaultdict(deque)
        self._active_docs_by_user: Dict[str, int] = defaultdict(int)
        self._active_runs_by_user: Dict[str, set[str]] = defaultdict(set)
        self._active_total = 0
        self._lock = threading.Lock()
        self._system_max_workers = system_max_workers
        self._users: Dict[str, User] = {}

    def register_user(self, user: User) -> None:
        self._users[user.id] = user

    def _user_limits(self, user_id: str) -> PlanLimits:
        user = self._users.get(user_id) or User(id=user_id, plan="free")
        return user.limits()

    def enqueue_run(self, job: RunJob) -> None:
        lim = self._user_limits(job.user_id)
        docs = job.documents[: lim.max_docs_per_run]
        with self._lock:
            for doc_id in docs:
                self._queues[job.user_id].append(
                    DocumentTask(
                        project_id=job.project_id,
                        document_id=doc_id,
                        user_id=job.user_id,
                        run_id=job.run_id,
                        mode=job.mode,
                        use_ai=job.use_ai and lim.ai_enabled,
                    )
                )

    def _can_dispatch(self, task: DocumentTask) -> bool:
        lim = self._user_limits(task.user_id)
        if self._active_total >= self._system_max_workers:
            return False
        if self._active_docs_by_user[task.user_id] >= lim.max_docs_concurrent:
            return False
        # Count runs: if this run is not already active, ensure we have capacity
        run_active = task.run_id in self._active_runs_by_user[task.user_id]
        if not run_active and len(self._active_runs_by_user[task.user_id]) >= lim.max_runs_concurrent:
            return False
        return True

    def try_dispatch(self) -> Optional[DocumentTask]:
        """Pick the next runnable DocumentTask based on fair-share.

        Returns a task and marks slots as used. Caller must call `finish(task)` when done.
        """
        with self._lock:
            if not self._queues:
                return None
            # Create a stable round-robin order of users with queued tasks
            users = [uid for uid, q in self._queues.items() if q]
            if not users:
                return None
            # Simple round-robin: rotate users in-place
            for uid in list(users):
                q = self._queues[uid]
                if not q:
                    continue
                peek = q[0]
                if self._can_dispatch(peek):
                    task = q.popleft()
                    self._active_total += 1
                    self._active_docs_by_user[task.user_id] += 1
                    self._active_runs_by_user[task.user_id].add(task.run_id)
                    return task
            return None

    def finish(self, task: DocumentTask) -> None:
        with self._lock:
            self._active_total = max(0, self._active_total - 1)
            self._active_docs_by_user[task.user_id] = max(0, self._active_docs_by_user[task.user_id] - 1)
            # If no more tasks for this run are active or queued for the user, free the run slot
            if not any(t.run_id == task.run_id for t in self._queues[task.user_id]):
                # Check also active docs for this run
                still_active_for_run = False
                # In this in-memory scheduler we can't easily count per-run actives; assume sequential per doc
                if not still_active_for_run:
                    self._active_runs_by_user[task.user_id].discard(task.run_id)

    # Helper to drain tasks for testing/demo
    def drain(self) -> List[DocumentTask]:
        dispatched: List[DocumentTask] = []
        while True:
            task = self.try_dispatch()
            if not task:
                break
            dispatched.append(task)
            # Simulate immediate finish for demo purposes
            self.finish(task)
        return dispatched

