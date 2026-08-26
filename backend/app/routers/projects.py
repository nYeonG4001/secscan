from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.project import Project, ProjectAccess
from app.schemas.project import ProjectAccessCreate, ProjectAccessOut, ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "ADMIN":
        return db.query(Project).all()
    accesses = (
        db.query(ProjectAccess).filter(ProjectAccess.user_id == current_user.id).all()
    )
    project_ids = [a.project_id for a in accesses]
    return db.query(Project).filter(Project.id.in_(project_ids)).all()


@router.post("/", response_model=ProjectOut)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    project = Project(name=body.name, created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    db.delete(project)
    db.commit()


@router.post("/{project_id}/access", response_model=ProjectAccessOut)
def grant_access(
    project_id: int,
    body: ProjectAccessCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    access = ProjectAccess(
        project_id=project_id, user_id=body.user_id, granted_by=current_user.id
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return access


@router.get("/{project_id}/access", response_model=List[ProjectAccessOut])
def list_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return db.query(ProjectAccess).filter(ProjectAccess.project_id == project_id).all()
