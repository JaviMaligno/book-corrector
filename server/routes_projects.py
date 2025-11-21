from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from .db import get_session
from .deps import get_current_user
from .models import Document, Project, Run, User

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/public")
def list_projects_public():
    """Endpoint público que devuelve información sobre proyectos sin requerir autenticación"""
    return {
        "message": "Para ver proyectos necesitas autenticación",
        "auth_required": True,
        "register_endpoint": "/auth/register",
        "login_endpoint": "/auth/login",
    }


class ProjectCreate(BaseModel):
    name: str
    lang_variant: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    lang_variant: str | None = None


class DocumentInfo(BaseModel):
    id: str
    name: str
    status: str = "ready"


class RunInfo(BaseModel):
    id: str
    status: str
    created_at: str


class ProjectDetail(BaseModel):
    id: str
    name: str
    documents: list[DocumentInfo]
    runs: list[RunInfo]


@router.get("", response_model=list[Project])
def list_projects(
    session: Session = Depends(get_session), current: User = Depends(get_current_user)
):
    return session.exec(select(Project).where(Project.owner_id == current.id)).all()


@router.post("", response_model=Project)
def create_project(
    req: ProjectCreate,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = Project(owner_id=current.id, name=req.name, lang_variant=req.lang_variant)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Get documents for this project
    docs = session.exec(select(Document).where(Document.project_id == project_id)).all()
    documents = [DocumentInfo(id=d.id, name=d.name, status="ready") for d in docs]

    # Get runs for this project
    runs_db = session.exec(
        select(Run).where(Run.project_id == project_id).order_by(Run.created_at.desc())
    ).all()
    runs = [
        RunInfo(
            id=r.id,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            created_at=r.created_at.isoformat(),
        )
        for r in runs_db
    ]

    return ProjectDetail(id=p.id, name=p.name, documents=documents, runs=runs)


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    req: ProjectUpdate,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if req.name is not None:
        p.name = req.name
    if req.lang_variant is not None:
        p.lang_variant = req.lang_variant
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Check if there are any runs associated with this project
    runs = session.exec(select(Run).where(Run.project_id == project_id)).all()
    if runs:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar un proyecto con ejecuciones. Elimina primero las ejecuciones."
        )

    # Delete associated documents first
    docs = session.exec(select(Document).where(Document.project_id == project_id)).all()
    for doc in docs:
        session.delete(doc)

    # Delete the project
    session.delete(p)
    session.commit()

    return {"message": "Proyecto eliminado exitosamente"}
