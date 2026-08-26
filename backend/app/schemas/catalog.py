from typing import Optional

from pydantic import BaseModel


class CatalogItemOut(BaseModel):
    kisa_code: str
    category: str
    name: str
    description: Optional[str] = None
    default_severity: str
    implementation_status: str
    semgrep_rule_id: Optional[str] = None

    model_config = {"from_attributes": True}
