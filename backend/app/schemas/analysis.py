from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AnalysisOut(BaseModel):
    id: int
    project_id: int
    executed_by: int
    engine: Optional[str] = None
    analyzed_languages: Optional[List[str]] = None
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    summary: Optional[dict] = None

    model_config = {"from_attributes": True}
