from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AnalysisUserOut(BaseModel):
    id: int
    project_id: int
    executed_by: int
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[dict] = None

    model_config = {"from_attributes": True}


class AnalysisAdminOut(AnalysisUserOut):
    # ADR-009: admin-only fields. engine/analyzed_languages/error_code/error_message
    # are internal execution detail; general failure guidance only for USER.
    engine: Optional[str] = None
    analyzed_languages: Optional[List[str]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
