from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .db import get_session
from .deps import get_current_user
from .limits import FREE, PREMIUM
from .models import (
    Document,
    DocumentKind,
    Export,
    Project,
    Run,
    RunDocument,
    RunDocumentStatus,
    RunMode,
    RunStatus,
    User,
)
from .scheduler import RunJob, User as SUser
from .scheduler_registry import get_scheduler

router = APIRouter(prefix="/runs", tags=["runs"])


class CreateRunRequest(BaseModel):
    project_id: str
    documents: list[str] = Field(default_factory=list, description="Document names (legacy)")
    document_ids: list[str] | None = Field(default=None, description="Preferred: Document IDs")
    mode: RunMode = Field(default=RunMode.rapido)
    use_ai: bool = True


class CreateRunResponse(BaseModel):
    run_id: str
    accepted_documents: list[str]
    queued: int


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    processed_documents: int
    total_documents: int


def _limits_for(role: str):
    return PREMIUM if role == "premium" else FREE


def _ensure_documents(session: Session, project_id: str, names: list[str]) -> list[Document]:
    docs: list[Document] = []
    for name in names:
        d = session.exec(
            select(Document).where(Document.project_id == project_id, Document.name == name)
        ).first()
        if not d:
            d = Document(project_id=project_id, name=name, kind=DocumentKind.docx)
            session.add(d)
            session.commit()
            session.refresh(d)
        docs.append(d)
    return docs


@router.post("", response_model=CreateRunResponse)
def create_run(
    req: CreateRunRequest,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    proj = session.get(Project, req.project_id)
    if not proj or proj.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    doc_ids: list[str] = req.document_ids or []
    if not doc_ids and not req.documents:
        raise HTTPException(status_code=400, detail="Debe indicar al menos un documento")

    run = Run(
        project_id=req.project_id,
        submitted_by=current.id,
        mode=req.mode,
        status=RunStatus.queued,
        params_json=json.dumps({"use_ai": req.use_ai}),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    docs: list[Document]
    if doc_ids:
        docs = []
        for did in doc_ids:
            d = session.get(Document, did)
            if not d or d.project_id != req.project_id:
                raise HTTPException(status_code=404, detail=f"Documento inválido: {did}")
            docs.append(d)
    else:
        # Legacy: create Document stubs by name if not exist
        docs = _ensure_documents(session, req.project_id, req.documents)
    # Create RunDocument entries
    for d in docs:
        rd = RunDocument(
            run_id=run.id, document_id=d.id, status=RunDocumentStatus.queued, use_ai=req.use_ai
        )
        session.add(rd)
    session.commit()

    # Enqueue into in-memory scheduler (fair-share) and respect per-plan limits
    role_value = current.role.value if hasattr(current.role, "value") else str(current.role)
    sched = get_scheduler()
    sched.register_user(SUser(id=current.id, plan=role_value))
    job = RunJob(
        user_id=current.id,
        run_id=run.id,
        project_id=req.project_id,
        documents=[d.id for d in docs],
        mode=req.mode.value,
        use_ai=req.use_ai,
    )
    sched.enqueue_run(job)
    # Dejar que el worker procese; inicialmente nada aceptado aún
    return CreateRunResponse(run_id=run.id, accepted_documents=[], queued=len(docs))


@router.get("/{run_id}", response_model=RunStatusResponse)
def get_run_status(
    run_id: str, session: Session = Depends(get_session), current: User = Depends(get_current_user)
):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    # Aggregate doc statuses
    rdocs = session.exec(select(RunDocument).where(RunDocument.run_id == run.id)).all()
    total = len(rdocs)
    processed = len([rd for rd in rdocs if rd.status == RunDocumentStatus.completed])
    status = (
        RunStatus.completed.value
        if processed == total and total > 0
        else (RunStatus.processing.value if processed > 0 else RunStatus.queued.value)
    )
    return RunStatusResponse(
        run_id=run.id, status=status, processed_documents=processed, total_documents=total
    )


# Exports listing and downloading
class ExportInfo(BaseModel):
    id: str
    kind: str
    name: str
    category: str
    size: int


def _categorize_export(path: str) -> str:
    name = os.path.basename(path).lower()
    if name.endswith(".corrections.jsonl"):
        return "log_jsonl"
    if name.endswith(".corrections.docx"):
        return "report_docx"
    if name.endswith(".changelog.csv"):
        return "changelog_csv"
    if name.endswith(".summary.md"):
        return "summary_md"
    if ".corrected." in name or name.endswith(".corrected.docx") or name.endswith(".corrected.txt"):
        return "corrected"
    return "other"


@router.get("/{run_id}/exports", response_model=list[ExportInfo])
def list_exports(
    run_id: str, session: Session = Depends(get_session), current: User = Depends(get_current_user)
):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
    results: list[ExportInfo] = []
    for e in exps:
        try:
            size = os.path.getsize(e.path)
        except Exception:
            size = 0
        results.append(
            ExportInfo(
                id=e.id,
                kind=e.kind.value if hasattr(e.kind, "value") else str(e.kind),
                name=os.path.basename(e.path),
                category=_categorize_export(e.path),
                size=size,
            )
        )
    return results


import csv
import json as _json

from fastapi.responses import FileResponse, StreamingResponse


@router.get("/{run_id}/exports/{export_id}/download")
def download_export(
    run_id: str,
    export_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    exp = session.get(Export, export_id)
    if not exp or exp.run_id != run_id:
        raise HTTPException(status_code=404, detail="Export no encontrado")
    filename = os.path.basename(exp.path)
    return FileResponse(exp.path, filename=filename)


@router.get("/{run_id}/exports/csv")
def export_csv(
    run_id: str, session: Session = Depends(get_session), current: User = Depends(get_current_user)
):
    # Aggregate all JSONL logs for the run into a single CSV
    exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
    jsonl_paths = [
        e.path
        for e in exps
        if str(getattr(e, "kind", "")) in {"jsonl", "ExportKind.jsonl"}
        or str(e.kind).endswith("jsonl")
        or os.path.basename(e.path).endswith(".jsonl")
    ]
    if not jsonl_paths:
        raise HTTPException(status_code=404, detail="No hay logs JSONL para este run")

    def iter_csv():
        out = io.StringIO()
        writer = csv.writer(out)
        header = [
            "document",
            "token_id",
            "line",
            "original",
            "corrected",
            "reason",
            "context",
            "chunk_index",
            "sentence",
        ]
        writer.writerow(header)
        yield out.getvalue()
        out.seek(0)
        out.truncate(0)
        for p in jsonl_paths:
            docname = os.path.basename(p).replace(".corrections.jsonl", "")
            try:
                with open(p, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = _json.loads(line)
                        except Exception:
                            continue
                        row = [
                            docname,
                            obj.get("token_id", ""),
                            obj.get("line", ""),
                            obj.get("original", ""),
                            obj.get("corrected", ""),
                            obj.get("reason", ""),
                            obj.get("context", ""),
                            obj.get("chunk_index", ""),
                            obj.get("sentence", ""),
                        ]
                        writer.writerow(row)
                        data = out.getvalue()
                        if data:
                            yield data
                            out.seek(0)
                            out.truncate(0)
            except FileNotFoundError:
                continue

    import io

    filename = f"run_{run_id}_changelog.csv"
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{run_id}/changelog.csv")
def get_persistent_changelog_csv(
    run_id: str, session: Session = Depends(get_session), current: User = Depends(get_current_user)
):
    # Prefer persistent CSV export if present
    exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
    for e in exps:
        if os.path.basename(e.path).lower().endswith(".changelog.csv"):
            return FileResponse(e.path, filename=os.path.basename(e.path), media_type="text/csv")

    # Fallback to on-the-fly aggregation if no persistent CSV found
    return export_csv(run_id, session=session, current=current)


@router.get("/{run_id}/summary.md")
def get_summary_md(
    run_id: str, session: Session = Depends(get_session), current: User = Depends(get_current_user)
):
    exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
    for e in exps:
        if os.path.basename(e.path).lower().endswith(".summary.md"):
            return FileResponse(
                e.path, filename=os.path.basename(e.path), media_type="text/markdown"
            )
    raise HTTPException(status_code=404, detail="Carta de edición no encontrada")


@router.get("/{run_id}/artifacts")
def list_artifacts(
    run_id: str, session: Session = Depends(get_session), current: User = Depends(get_current_user)
):
    """Alias de /exports que devuelve lista de nombres de archivo"""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
    files = [os.path.basename(e.path) for e in exps if os.path.exists(e.path)]
    return {"files": files}


# Endpoint para descargar artifacts por nombre de archivo (para compatibilidad con frontend legacy)
@router.get("/artifacts/{run_id}/{filename}")
def download_artifact_by_filename(
    run_id: str, filename: str, session: Session = Depends(get_session)
):
    """Download artifact by filename (legacy endpoint for frontend compatibility)"""
    # Buscar el export que coincida con el nombre de archivo
    exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
    for exp in exps:
        if os.path.basename(exp.path) == filename:
            if os.path.exists(exp.path):
                return FileResponse(exp.path, filename=filename)
            else:
                raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    raise HTTPException(status_code=404, detail=f"Artifact not found: {filename}")
