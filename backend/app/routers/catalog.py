from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.kisa_catalog import KisaCatalog
from app.schemas.catalog import CatalogItemCreate, CatalogItemOut, CatalogItemUpdate

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


@router.post("/", response_model=CatalogItemOut, status_code=201)
def create_catalog_item(
    body: CatalogItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if db.get(KisaCatalog, body.kisa_code):
        raise HTTPException(status_code=409, detail="이미 등록된 kisa_code입니다.")
    item = KisaCatalog(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{kisa_code}", response_model=CatalogItemOut)
def update_catalog_item(
    kisa_code: str,
    body: CatalogItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    item = db.get(KisaCatalog, kisa_code)
    if not item:
        raise HTTPException(status_code=404, detail="카탈로그 항목을 찾을 수 없습니다.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item
