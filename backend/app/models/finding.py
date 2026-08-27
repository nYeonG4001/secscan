from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("analyses.id"), nullable=False)
    kisa_code: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("kisa_catalog.kisa_code"), nullable=True
    )
    # ADR-005: snapshot fields — copied at analysis time, independent of catalog changes.
    # Unmapped results (kisa_code IS NULL) leave criterion_id NULL as well.
    criterion_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rule_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ADR-007: snapshot of the catalog's default recommendation at normalization time.
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ADR-009: admin-only field. Role-based response filtering is E1-07's job.
    raw_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    analysis = relationship("Analysis", back_populates="findings")
    kisa_item = relationship("KisaCatalog", back_populates="findings")
