from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


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
    source_status: Literal["NEEDS_UPLOAD", "REGISTERED"]
    latest_analysis_status: Optional[Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceUploadOut(BaseModel):
    project_id: int
    source_status: str
    target_languages: List[str]


class ProjectAccessCreate(BaseModel):
    email: EmailStr


class ProjectAccessOut(BaseModel):
    id: int
    project_id: int
    user_id: int
    user_email: EmailStr
    granted_at: datetime
    granted_by: int

    model_config = {"from_attributes": True}
