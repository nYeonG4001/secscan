from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    get_current_user,
    get_project_for_current_user,
    require_admin,
    require_csrf,
)
from app.models.project import Project, ProjectAccess
from app.models.user import User
from app.schemas.project import (
    ProjectAccessCreate,
    ProjectAccessOut,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_project_access_out(access: ProjectAccess) -> ProjectAccessOut:
    return ProjectAccessOut(
        id=access.id,
        project_id=access.project_id,
        user_id=access.user_id,
        user_email=access.user.email,
        granted_at=access.granted_at,
        granted_by=access.granted_by,
    )


def _unique_display_name(
    db: Session, name: str, *, exclude_project_id: Optional[int] = None
) -> str:
    def _taken(candidate: str) -> bool:
        query = db.query(Project).filter(Project.name == candidate)
        if exclude_project_id is not None:
            query = query.filter(Project.id != exclude_project_id)
        return db.query(query.exists()).scalar()

    if not _taken(name):
        return name
    suffix = 1
    while True:
        candidate = f"{name} ({suffix})"
        if not _taken(candidate):
            return candidate
        suffix += 1


@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "ADMIN":
        return db.query(Project).all()
    accesses = (
        db.query(ProjectAccess).filter(ProjectAccess.user_id == current_user.id).all()
    )
    project_ids = [a.project_id for a in accesses]
    return db.query(Project).filter(Project.id.in_(project_ids)).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project: Project = Depends(get_project_for_current_user)):
    return project


@router.post("/", response_model=ProjectOut)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
):
    name = _unique_display_name(db, body.name)
    project = Project(name=name, description=body.description, created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    if body.name is not None:
        project.name = _unique_display_name(db, body.name, exclude_project_id=project_id)
    if body.description is not None:
        project.description = body.description
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/access", response_model=ProjectAccessOut)
def grant_access(
    project_id: int,
    body: ProjectAccessCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.role != "USER":
        raise HTTPException(
            status_code=422,
            detail="일반 사용자에게만 접근권한을 부여할 수 있습니다.",
        )
    if (
        db.query(ProjectAccess)
        .filter(ProjectAccess.project_id == project_id, ProjectAccess.user_id == user.id)
        .first()
    ):
        raise HTTPException(status_code=409, detail="이미 접근권한이 부여되었습니다.")
    access = ProjectAccess(
        project_id=project_id, user_id=user.id, granted_by=current_user.id
    )
    db.add(access)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 접근권한이 부여되었습니다.")
    db.refresh(access)
    return _to_project_access_out(access)


@router.get("/{project_id}/access", response_model=List[ProjectAccessOut])
def list_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    accesses = db.query(ProjectAccess).filter(ProjectAccess.project_id == project_id).all()
    return [_to_project_access_out(access) for access in accesses]


@router.delete("/{project_id}/access/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_access(
    project_id: int,
    user_id: int,
    response: Response,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
) -> None:
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    access = (
        db.query(ProjectAccess)
        .filter(ProjectAccess.project_id == project_id, ProjectAccess.user_id == user_id)
        .first()
    )
    if not access:
        raise HTTPException(status_code=404, detail="프로젝트 접근권한을 찾을 수 없습니다.")
    db.delete(access)
    db.commit()
