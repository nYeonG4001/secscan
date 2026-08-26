from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime

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
