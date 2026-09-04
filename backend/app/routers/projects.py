import logging
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    get_current_user,
    get_project_for_current_user,
    get_source_workspace,
    get_upload_locks,
    require_admin,
    require_csrf,
)
from app.models.analysis import Analysis
from app.models.project import Project, ProjectAccess
from app.models.user import User
from app.schemas.project import (
    ProjectAccessCreate,
    ProjectAccessOut,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    SourcePreflightOut,
    SourceUploadOut,
)
from app.services.project_upload_lock import ProjectUploadLocks, UploadInProgressError
from app.services.source_archive import (
    NoSupportedSourceError,
    SourceArchiveError,
    SourceArchiveLimitExceededError,
    SourceArchiveTooLargeError,
    UnsafeSourceArchiveError,
    extract_source_archive,
)
from app.services.source_workspace import SourceWorkspace

logger = logging.getLogger(__name__)

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


def _to_project_out(project: Project, latest_analysis_status: Optional[str] = None) -> ProjectOut:
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        source_type=project.source_type,
        target_languages=project.target_languages,
        source_status="REGISTERED" if project.source_location else "NEEDS_UPLOAD",
        latest_analysis_status=latest_analysis_status,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _latest_analysis_statuses(db: Session, project_ids: List[int]) -> dict[int, str]:
    if not project_ids:
        return {}

    latest_analysis_ids = (
        db.query(
            Analysis.project_id.label("project_id"),
            func.max(Analysis.id).label("analysis_id"),
        )
        .filter(Analysis.project_id.in_(project_ids))
        .group_by(Analysis.project_id)
        .subquery()
    )
    return dict(
        db.query(Analysis.project_id, Analysis.status)
        .join(latest_analysis_ids, Analysis.id == latest_analysis_ids.c.analysis_id)
        .all()
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
        projects = db.query(Project).order_by(Project.updated_at.desc(), Project.id.desc()).all()
    else:
        accesses = (
            db.query(ProjectAccess).filter(ProjectAccess.user_id == current_user.id).all()
        )
        project_ids = [access.project_id for access in accesses]
        projects = (
            db.query(Project)
            .filter(Project.id.in_(project_ids))
            .order_by(Project.updated_at.desc(), Project.id.desc())
            .all()
        )
    latest_statuses = _latest_analysis_statuses(db, [project.id for project in projects])
    return [_to_project_out(project, latest_statuses.get(project.id)) for project in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project: Project = Depends(get_project_for_current_user),
    db: Session = Depends(get_db),
):
    return _to_project_out(project, _latest_analysis_statuses(db, [project.id]).get(project.id))


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
    return _to_project_out(project)


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
    return _to_project_out(project, _latest_analysis_statuses(db, [project.id]).get(project.id))


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


@router.put("/{project_id}/source", response_model=SourceUploadOut)
def upload_source(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
    workspace: SourceWorkspace = Depends(get_source_workspace),
    upload_locks: ProjectUploadLocks = Depends(get_upload_locks),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    active_analysis = (
        db.query(Analysis)
        .filter(
            Analysis.project_id == project_id,
            Analysis.status.in_(["PENDING", "RUNNING"]),
        )
        .first()
    )
    if active_analysis:
        return JSONResponse(status_code=409, content={"code": "ANALYSIS_ACTIVE"})

    try:
        with upload_locks.acquire(project_id):
            return _process_source_upload(project, file, workspace, db)
    except UploadInProgressError:
        return JSONResponse(status_code=409, content={"code": "UPLOAD_IN_PROGRESS"})


@router.post("/{project_id}/source/preflight", response_model=SourcePreflightOut)
def preflight_source(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
    workspace: SourceWorkspace = Depends(get_source_workspace),
):
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    try:
        with workspace.staging_directory() as staging_dir:
            extract_source_archive(file.file, staging_dir)
        return SourcePreflightOut()
    except SourceArchiveTooLargeError:
        return JSONResponse(status_code=413, content={"code": "ARCHIVE_TOO_LARGE"})
    except SourceArchiveLimitExceededError:
        return JSONResponse(status_code=422, content={"code": "ARCHIVE_LIMIT_EXCEEDED"})
    except UnsafeSourceArchiveError:
        return JSONResponse(status_code=422, content={"code": "UNSAFE_ARCHIVE"})
    except NoSupportedSourceError:
        return JSONResponse(status_code=422, content={"code": "NO_SUPPORTED_SOURCE"})
    except SourceArchiveError:
        logger.exception("Archive preflight error for project %d", project_id)
        return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR"})


def _process_source_upload(
    project: Project,
    file: UploadFile,
    workspace: SourceWorkspace,
    db: Session,
) -> SourceUploadOut | JSONResponse:
    staging_dir = workspace.create_staging_directory()
    promoted_location: str | None = None

    try:
        result = extract_source_archive(file.file, staging_dir)
        promoted_location = workspace.promote_staging_directory(project.id, staging_dir)

        project.source_type = "FILE_UPLOAD"
        project.target_languages = list(result.languages)
        project.source_location = promoted_location

        try:
            db.commit()
        except Exception:
            db.rollback()
            _cleanup_promoted_location(workspace, promoted_location)
            promoted_location = None
            logger.exception(
                "DB commit failed during source upload for project %d", project.id
            )
            return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR"})

        return SourceUploadOut(
            project_id=project.id,
            source_status="REGISTERED",
            target_languages=list(result.languages),
        )

    except SourceArchiveTooLargeError:
        return JSONResponse(status_code=413, content={"code": "ARCHIVE_TOO_LARGE"})
    except SourceArchiveLimitExceededError:
        return JSONResponse(status_code=422, content={"code": "ARCHIVE_LIMIT_EXCEEDED"})
    except UnsafeSourceArchiveError:
        return JSONResponse(status_code=422, content={"code": "UNSAFE_ARCHIVE"})
    except NoSupportedSourceError:
        return JSONResponse(status_code=422, content={"code": "NO_SUPPORTED_SOURCE"})
    except SourceArchiveError:
        logger.exception("Archive validation error for project %d", project.id)
        return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR"})
    except Exception:
        logger.exception(
            "Unexpected error during source upload for project %d", project.id
        )
        if promoted_location:
            _cleanup_promoted_location(workspace, promoted_location)
        return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR"})
    finally:
        workspace.cleanup_staging_directory(staging_dir)


def _cleanup_promoted_location(workspace: SourceWorkspace, location: str) -> None:
    try:
        path = workspace.resolve_source_location(location)
        if path.is_dir():
            shutil.rmtree(path)
    except Exception:
        logger.exception("Failed to cleanup promoted source at %s", location)
