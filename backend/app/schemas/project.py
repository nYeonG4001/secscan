from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    source_type: Optional[str] = None
    target_languages: Optional[List[str]] = None
    source_location: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectAccessCreate(BaseModel):
    user_id: int


class ProjectAccessOut(BaseModel):
    id: int
    project_id: int
    user_id: int
    granted_at: datetime
    granted_by: int

    model_config = {"from_attributes": True}
