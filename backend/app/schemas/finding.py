from typing import Optional

from pydantic import BaseModel


class FindingOut(BaseModel):
    id: int
    analysis_id: int
    kisa_code: Optional[str] = None
    # ADR-005 snapshot fields
    rule_name: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None
    language: Optional[str] = None
    file_path: str
    line: Optional[int] = None
    message: Optional[str] = None
    code_snippet: Optional[str] = None

    model_config = {"from_attributes": True}
