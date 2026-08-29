from typing import Optional

from pydantic import BaseModel


class CatalogItemOut(BaseModel):
    kisa_code: str
    criterion_id: Optional[str] = None
    item_number: Optional[int] = None
    category: str
    name: str
    description: Optional[str] = None
    reference_info: Optional[str] = None
    default_severity: str
    active: bool
    implementation_status: str
    recommendation: Optional[str] = None

    model_config = {"from_attributes": True}


class CatalogItemCreate(BaseModel):
    kisa_code: str
    name: str
    description: Optional[str] = None
    criterion_id: Optional[str] = None
    category: str
    item_number: Optional[int] = None
    reference_info: Optional[str] = None
    active: bool = True
    default_severity: str
    implementation_status: str = "미지원"

    model_config = {"extra": "forbid"}


class CatalogItemUpdate(BaseModel):
    description: Optional[str] = None
    reference_info: Optional[str] = None
    active: Optional[bool] = None
    default_severity: Optional[str] = None
    implementation_status: Optional[str] = None
    recommendation: Optional[str] = None

    model_config = {"extra": "forbid"}
