from __future__ import annotations

import os
import logging
from typing import Dict

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
except Exception:  # pragma: no cover - only needed when running the server
    FastAPI = None  # type: ignore
    HTTPException = Exception  # type: ignore
    CORSMiddleware = None  # type: ignore

from sqlmodel import select

# Configure logging for the corrector engine
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S',
    force=True  # Override any existing configuration
)

from .db import init_db, session_scope
from .limits import FREE, PREMIUM, SYSTEM_MAX_WORKERS
from .schemas import MeLimits
from .routes_auth import router as auth_router
from .routes_projects import router as projects_router
from .routes_runs import router as runs_router
from .routes_documents import router as documents_router
from .routes_suggestions import router as suggestions_router
from .models import RunDocument, Run, User, RunDocumentStatus, Suggestion
from .scheduler_registry import get_scheduler
from .scheduler import RunJob, User as SUser


def create_app() -> "FastAPI":  # type: ignore
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Please `pip install fastapi uvicorn`.\n" )
    app = FastAPI(title="Corrector Backend", version="0.1")

    # CORS middleware
    if CORSMiddleware is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Init DB tables
    init_db()

    # Health
    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Limits for demo (per plan)
    @app.get("/me/limits", response_model=MeLimits)
    def me_limits():
        plan = os.environ.get("DEMO_PLAN", "free")
        limits = PREMIUM if plan == "premium" else FREE
        return MeLimits(
            plan=limits.name,
            max_runs_concurrent=limits.max_runs_concurrent,
            max_docs_per_run=limits.max_docs_per_run,
            max_docs_concurrent=limits.max_docs_concurrent,
            rate_limit_rpm=limits.rate_limit_rpm,
            ai_enabled=limits.ai_enabled,
        )

    # Artifacts download endpoint (global, not under /runs prefix)
    @app.get("/artifacts/{run_id}/{filename}")
    def download_artifact(run_id: str, filename: str):
        from fastapi.responses import FileResponse
        from .models import Export
        from .db import engine
        from sqlmodel import Session

        with Session(engine) as session:
            exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
            for exp in exps:
                if os.path.basename(exp.path) == filename:
                    if os.path.exists(exp.path):
                        return FileResponse(exp.path, filename=filename)
                    else:
                        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
            raise HTTPException(status_code=404, detail=f"Artifact not found: {filename}")

    # Routers
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(runs_router)
    app.include_router(documents_router)
    app.include_router(suggestions_router)

    # Startup background worker and rebuild scheduler from DB (persistent queue)
    try:
        from .worker import Worker

        _worker = Worker()
        print("✅ Worker initialized successfully")

        @app.on_event("startup")
        def _start_worker():  # pragma: no cover
            print("🚀 Starting worker...")

            # Ensure demo user exists with correct plan
            try:
                with session_scope() as session:
                    from .auth import hash_password
                    demo_plan = os.environ.get("DEMO_PLAN", "free")
                    demo_user = session.exec(select(User).where(User.email == "demo@example.com")).first()
                    if not demo_user:
                        demo_user = User(
                            email="demo@example.com",
                            password_hash=hash_password("demo123"),
                            role=demo_plan
                        )
                        session.add(demo_user)
                        session.commit()
                        print(f"✅ Created demo user: demo@example.com / demo123 (plan: {demo_plan})")
                    else:
                        # Update role if plan changed
                        if demo_user.role != demo_plan:
                            demo_user.role = demo_plan
                            session.add(demo_user)
                            session.commit()
                            print(f"✅ Updated demo user plan: {demo_plan}")
                        else:
                            print(f"✅ Demo user already exists (plan: {demo_plan})")
            except Exception as e:
                print(f"⚠️  Error ensuring demo user: {e}")

            # Setup demo data with sample corrections
            try:
                from .demo_data import setup_demo_data
                setup_demo_data()
            except Exception as e:
                print(f"⚠️  Error setting up demo data: {e}")

            # Rebuild the in-memory scheduler from queued tasks in DB
            try:
                with session_scope() as session:
                    rows = session.exec(
                        select(RunDocument, Run)
                        .join(Run, Run.id == RunDocument.run_id)
                        .where(RunDocument.status == RunDocumentStatus.queued)
                    ).all()
                    print(f"📋 Found {len(rows)} queued tasks to rebuild")
                    for rd, run in rows:
                        user = session.get(User, run.submitted_by)
                        plan = (user.role.value if hasattr(user, "role") else "free") if user else "free"
                        get_scheduler().register_user(SUser(id=run.submitted_by, plan=plan))
                        job = RunJob(
                            user_id=run.submitted_by,
                            run_id=run.id,
                            project_id=run.project_id,
                            documents=[rd.document_id],
                            mode=run.mode.value if hasattr(run.mode, "value") else str(run.mode),
                            use_ai=rd.use_ai if hasattr(rd, 'use_ai') else False,
                        )
                        get_scheduler().enqueue_run(job)
            except Exception as e:
                print(f"⚠️  Error rebuilding scheduler: {e}")
            _worker.start()
            print("✅ Worker started successfully")

        @app.on_event("shutdown")
        def _stop_worker():  # pragma: no cover
            print("🛑 Stopping worker...")
            _worker.stop()
    except Exception as e:
        # Worker not started if dependencies are missing
        print(f"❌ Worker failed to initialize: {e}")
        import traceback
        traceback.print_exc()

    return app


app = None
try:  # pragma: no cover
    app = create_app()
except RuntimeError:
    # FastAPI not installed; app remains None for environments without server deps.
    pass
