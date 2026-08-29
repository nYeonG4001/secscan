from typing import Annotated, Literal, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_project_for_current_user
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.schemas.finding import FindingAdminOut, FindingListItemOut, FindingListOut, FindingUserOut

router = APIRouter(prefix="/findings", tags=["findings"])


def _to_finding_out(finding: Finding, current_user) -> Union[FindingAdminOut, FindingUserOut]:
    # ADR-009: explicit role-specific response models, not conditional field masking.
    if current_user.role == "ADMIN":
        return FindingAdminOut.model_validate(finding)
    return FindingUserOut.model_validate(finding)


def _to_finding_list_item(finding: Finding) -> FindingListItemOut:
    return FindingListItemOut(
        id=finding.id,
        severity=finding.severity,
        rule_name=finding.rule_name,
        kisa_code=finding.kisa_code,
        file_path=finding.file_path,
        line=finding.line,
        end_line=finding.end_line,
        language=finding.language,
        confidence=finding.confidence,
        mapping_status="KISA_MAPPED" if finding.kisa_code else "UNMAPPED",
    )


@router.get("/", response_model=FindingListOut)
def list_findings(
    analysis_id: int,
    severity: Optional[str] = None,
    mapping_status: Optional[Literal["KISA_MAPPED", "UNMAPPED"]] = None,
    language: Optional[Literal["JAVA", "JAVASCRIPT", "PYTHON"]] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
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
    if mapping_status == "KISA_MAPPED":
        q = q.filter(Finding.kisa_code.is_not(None))
    elif mapping_status == "UNMAPPED":
        q = q.filter(Finding.kisa_code.is_(None))
    if language:
        q = q.filter(Finding.language == language)

    total = q.count()
    severity_order = case(
        (Finding.severity == "CRITICAL", 0),
        (Finding.severity == "HIGH", 1),
        (Finding.severity == "MEDIUM", 2),
        (Finding.severity == "LOW", 3),
        else_=4,
    )
    findings = (
        q.order_by(
            severity_order,
            Finding.file_path.asc().nulls_last(),
            Finding.line.asc().nulls_last(),
            Finding.id.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return FindingListOut(
        items=[_to_finding_list_item(finding) for finding in findings],
        total=total,
        limit=limit,
        offset=offset,
    )


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
