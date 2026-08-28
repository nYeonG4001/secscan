from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_project_for_current_user
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.schemas.finding import FindingAdminOut, FindingUserOut

router = APIRouter(prefix="/findings", tags=["findings"])


def _to_finding_out(finding: Finding, current_user) -> Union[FindingAdminOut, FindingUserOut]:
    # ADR-009: explicit role-specific response models, not conditional field masking.
    if current_user.role == "ADMIN":
        return FindingAdminOut.model_validate(finding)
    return FindingUserOut.model_validate(finding)


@router.get("/", response_model=List[Union[FindingAdminOut, FindingUserOut]])
def list_findings(
    analysis_id: int,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다.")
    get_project_for_current_user(analysis.project_id, db=db, current_user=current_user)
    q = db.query(Finding).filter(Finding.analysis_id == analysis_id)
    if severity:
        q = q.filter(Finding.severity == severity)
    return [_to_finding_out(finding, current_user) for finding in q.all()]


@router.get("/{finding_id}", response_model=Union[FindingAdminOut, FindingUserOut])
def get_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")
    analysis = db.get(Analysis, finding.analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")
    get_project_for_current_user(analysis.project_id, db=db, current_user=current_user)
    return _to_finding_out(finding, current_user)
