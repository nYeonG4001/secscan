from typing import Optional

from pydantic import BaseModel


class FindingUserOut(BaseModel):
    id: int
    analysis_id: int
    kisa_code: Optional[str] = None
    criterion_id: Optional[str] = None
    engine_rule_id: str
    rule_name: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None
    language: Optional[str] = None
    file_path: str
    line: Optional[int] = None
    end_line: Optional[int] = None
    message: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    code_snippet: Optional[str] = None

    model_config = {"from_attributes": True}


class FindingAdminOut(FindingUserOut):
    raw_result: Optional[dict] = None
