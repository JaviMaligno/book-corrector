from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from .db import get_session
from .deps import get_current_user
from .models import Document, DocumentKind, DocumentStatus, Project, User
from .storage import save_upload_for_project

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


@router.get("", response_model=list[Document])
def list_documents(
    project_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    docs = session.exec(select(Document).where(Document.project_id == project_id)).all()
    return docs


@router.post("/upload", response_model=list[Document])
def upload_documents(
    project_id: str,
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if not files:
        raise HTTPException(status_code=400, detail="No se adjuntaron archivos")

    saved_docs: list[Document] = []
    for up in files:
        # FastAPI can't easily give size without reading; we trust this limit at reverse proxy in production
        dest_path, checksum, kind = save_upload_for_project(
            user_id=current.id, project_id=project_id, up=up
        )
        # Generate a display name unique per project if needed
        name = up.filename or dest_path.name
        existing = session.exec(
            select(Document).where(Document.project_id == project_id, Document.name == name)
        ).first()
        if existing:
            # allow multiple versions; append suffix
            base, ext = os.path.splitext(name)
            idx = 1
            new_name = f"{base} ({idx}){ext}"
            while session.exec(
                select(Document).where(Document.project_id == project_id, Document.name == new_name)
            ).first():
                idx += 1
                new_name = f"{base} ({idx}){ext}"
            name = new_name

        doc = Document(
            project_id=project_id,
            name=name,
            path=str(dest_path),
            kind=DocumentKind(kind),
            checksum=checksum,
            status=DocumentStatus.ready,
        )
        session.add(doc)
        saved_docs.append(doc)

    # Commit all documents at once
    session.commit()

    # Refresh all documents to get their generated IDs
    for doc in saved_docs:
        session.refresh(doc)

    return saved_docs


@router.get("/{document_id}", response_model=Document)
def get_document(
    project_id: str,
    document_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    d = session.get(Document, document_id)
    if not d or d.project_id != project_id:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return d


@router.get("/{document_id}/download")
def download_document(
    project_id: str,
    document_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    d = session.get(Document, document_id)
    if not d or d.project_id != project_id:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if not d.path:
        raise HTTPException(status_code=404, detail="Documento sin archivo")
    return FileResponse(d.path, filename=d.name)
