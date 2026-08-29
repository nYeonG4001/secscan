from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KisaCatalog(Base):
    __tablename__ = "kisa_catalog"
    __table_args__ = (
        CheckConstraint(
            "implementation_status IN ('지원', '부분 지원', '미지원')",
            name="ck_kisa_catalog_implementation_status",
        ),
        CheckConstraint(
            "default_severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')",
            name="ck_kisa_catalog_default_severity",
        ),
    )

    kisa_code: Mapped[str] = mapped_column(String, primary_key=True)
    criterion_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    item_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_severity: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    implementation_status: Mapped[str] = mapped_column(
        String, nullable=False, default="미지원"
    )
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    findings = relationship("Finding", back_populates="kisa_item")
