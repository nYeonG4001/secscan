from typing import Optional

from pydantic import BaseModel


class FindingUserOut(BaseModel):
    id: int
    analysis_id: int
    kisa_code: Optional[str] = None
    # ADR-005 snapshot fields
    criterion_id: Optional[str] = None
    rule_name: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None
    language: Optional[str] = None
    file_path: str
    line: Optional[int] = None
    message: Optional[str] = None
    evidence: Optional[str] = None
    # ADR-007 snapshot field
    recommendation: Optional[str] = None
    code_snippet: Optional[str] = None

    model_config = {"from_attributes": True}


class FindingAdminOut(FindingUserOut):
    # ADR-009: admin-only field
    raw_result: Optional[dict] = None
