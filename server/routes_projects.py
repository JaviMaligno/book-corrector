from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from .deps import get_current_user
from .db import get_session
from .models import Project, User


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/public")
def list_projects_public():
    """Endpoint público que devuelve información sobre proyectos sin requerir autenticación"""
    return {
        "message": "Para ver proyectos necesitas autenticación",
        "auth_required": True,
        "register_endpoint": "/auth/register",
        "login_endpoint": "/auth/login"
    }


class ProjectCreate(BaseModel):
    name: str
    lang_variant: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    lang_variant: str | None = None


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


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user),
):
    p = session.get(Project, project_id)
    if not p or p.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return p


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

