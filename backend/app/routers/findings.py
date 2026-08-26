from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.finding import Finding
from app.schemas.finding import FindingOut

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("/", response_model=List[FindingOut])
def list_findings(
    analysis_id: int,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Finding).filter(Finding.analysis_id == analysis_id)
    if severity:
        q = q.filter(Finding.severity == severity)
    return q.all()


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")
    return finding
