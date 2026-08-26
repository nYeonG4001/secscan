from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.kisa_catalog import KisaCatalog
from app.schemas.catalog import CatalogItemOut

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/", response_model=List[CatalogItemOut])
def list_catalog(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(KisaCatalog).order_by(KisaCatalog.kisa_code).all()


@router.get("/{kisa_code}", response_model=CatalogItemOut)
def get_catalog_item(
    kisa_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = db.get(KisaCatalog, kisa_code)
    if not item:
        raise HTTPException(status_code=404, detail="카탈로그 항목을 찾을 수 없습니다.")
    return item
