from typing import List, Union

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    get_current_user,
    get_project_for_current_user,
    require_admin,
    require_csrf,
)
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisAdminOut, AnalysisUserOut

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _to_analysis_out(analysis: Analysis, current_user) -> Union[AnalysisAdminOut, AnalysisUserOut]:
    # ADR-009: explicit role-specific response models, not conditional field masking.
    if current_user.role == "ADMIN":
        return AnalysisAdminOut.model_validate(analysis)
    return AnalysisUserOut.model_validate(analysis)


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


@router.post("/", response_model=AnalysisAdminOut)
def create_analysis(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _: None = Depends(require_csrf),
):
    # Stub: file saved and Semgrep execution queued in a later sprint
    analysis = Analysis(
        project_id=project_id, executed_by=current_user.id, status="PENDING"
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis
