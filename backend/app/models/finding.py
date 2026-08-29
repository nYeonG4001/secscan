from typing import Optional
from uuid import uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        CheckConstraint(
            "end_line IS NULL OR end_line >= line",
            name="ck_findings_end_line_gte_line",
        ),
        CheckConstraint(
            "severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')",
            name="ck_findings_severity",
        ),
        CheckConstraint(
            "confidence IN ('HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')",
            name="ck_findings_confidence",
        ),
        UniqueConstraint(
            "analysis_id", "finding_fingerprint",
            name="uq_findings_analysis_fingerprint",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("analyses.id"), nullable=False)
    kisa_code: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("kisa_catalog.kisa_code"), nullable=True
    )
    criterion_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    engine_rule_id: Mapped[str] = mapped_column(String, nullable=False, default="legacy.unknown")
    rule_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finding_fingerprint: Mapped[str] = mapped_column(
        String, nullable=False, default=lambda: uuid4().hex
    )

    analysis = relationship("Analysis", back_populates="findings")
    kisa_item = relationship("KisaCatalog", back_populates="findings")
