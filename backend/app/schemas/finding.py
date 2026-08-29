from typing import Literal, Optional

from pydantic import BaseModel


class FindingListItemOut(BaseModel):
    id: int
    kisa_code: Optional[str] = None
    rule_name: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None
    language: Optional[str] = None
    file_path: str
    line: Optional[int] = None
    end_line: Optional[int] = None
    mapping_status: Literal["KISA_MAPPED", "UNMAPPED"]

    model_config = {"from_attributes": True}


class FindingUserOut(FindingListItemOut):
    analysis_id: int
    criterion_id: Optional[str] = None
    engine_rule_id: str
    message: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    code_snippet: Optional[str] = None


class FindingAdminOut(FindingUserOut):
    raw_result: Optional[dict] = None


class FindingListOut(BaseModel):
    items: list[FindingListItemOut]
    total: int
    limit: int
    offset: int
