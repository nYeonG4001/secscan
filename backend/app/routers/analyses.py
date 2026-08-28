from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    get_analysis_executor,
    get_current_user,
    get_project_for_current_user,
    get_source_workspace,
    get_upload_locks,
    require_admin,
    require_csrf,
)
from app.models.analysis import Analysis
from app.models.project import Project
from app.schemas.analysis import AnalysisAdminOut, AnalysisCreate, AnalysisUserOut
from app.services.analysis_executor import AnalysisExecutor
from app.services.project_upload_lock import ProjectUploadLocks, UploadInProgressError
from app.services.source_workspace import SourceWorkspace

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _to_analysis_out(analysis: Analysis, current_user) -> Union[AnalysisAdminOut, AnalysisUserOut]:
    if current_user.role == "ADMIN":
        return AnalysisAdminOut.model_validate(analysis)
    return AnalysisUserOut.model_validate(analysis)


def _active_analysis_response(analysis: Analysis) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"code": "ANALYSIS_ACTIVE", "analysis_id": analysis.id, "status": analysis.status},
    )


@router.get("/", response_model=List[Union[AnalysisAdminOut, AnalysisUserOut]])
def list_analyses(
    project=Depends(get_project_for_current_user),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    analyses = db.query(Analysis).filter(Analysis.project_id == project.id).all()
    return [_to_analysis_out(analysis, current_user) for analysis in analyses]


@router.get("/{analysis_id}", response_model=Union[AnalysisAdminOut, AnalysisUserOut])
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다.")
    get_project_for_current_user(analysis.project_id, db=db, current_user=current_user)
    return _to_analysis_out(analysis, current_user)


@router.post("/", response_model=AnalysisAdminOut, status_code=status.HTTP_201_CREATED)
def create_analysis(
    body: AnalysisCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
    workspace: SourceWorkspace = Depends(get_source_workspace),
    upload_locks: ProjectUploadLocks = Depends(get_upload_locks),
    executor: AnalysisExecutor = Depends(get_analysis_executor),
):
    try:
        with upload_locks.acquire(body.project_id):
            project = db.get(Project, body.project_id)
            if not project:
                raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
            if not project.source_location:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"code": "SOURCE_NOT_REGISTERED"},
                )
            active = (
                db.query(Analysis)
                .filter(
                    Analysis.project_id == project.id,
                    Analysis.status.in_(["PENDING", "RUNNING"]),
                )
                .first()
            )
            if active:
                return _active_analysis_response(active)

            analysis = Analysis(
                project_id=project.id,
                executed_by=current_user.id,
                engine="semgrep",
                analyzed_languages=list(project.target_languages or []),
                source_location=project.source_location,
                status="PENDING",
            )
            db.add(analysis)
            try:
                db.flush()
                analysis.source_snapshot_location = workspace.reserve_analysis_snapshot(analysis.id)
                db.commit()
            except IntegrityError:
                db.rollback()
                active = (
                    db.query(Analysis)
                    .filter(
                        Analysis.project_id == project.id,
                        Analysis.status.in_(["PENDING", "RUNNING"]),
                    )
                    .first()
                )
                if active:
                    return _active_analysis_response(active)
                raise
            except Exception:
                db.rollback()
                raise
            db.refresh(analysis)
    except UploadInProgressError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"code": "SOURCE_UPLOAD_IN_PROGRESS"},
        )

    executor.submit(analysis.id)
    return analysis
