from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalysisOut(BaseModel):
    id: int
    project_id: int
    executed_by: int
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
