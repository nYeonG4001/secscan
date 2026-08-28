from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="ck_analyses_status",
        ),
        # DAR-005 decision: at most one PENDING/RUNNING analysis per project,
        # enforced at the DB level via a partial unique index.
        Index(
            "uq_analyses_project_active",
            "project_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'RUNNING')"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    executed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    # Analysis engine or method used for this run (e.g. "semgrep").
    engine: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Snapshot of auto-identified languages at analysis creation time (ADR-006);
    # does not change if the project's target_languages changes later.
    analyzed_languages: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    # System-managed snapshot location; never included in any API response (ADR-009).
    source_snapshot_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Source location captured at request commit time. This internal field lets the
    # worker copy exactly the source selected for the pending analysis.
    source_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="PENDING"
    )  # PENDING/RUNNING/COMPLETED/FAILED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # FAILED detail code (timeout, invalid file, engine error, ...); admin-only (ADR-009).
    error_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Recent, scrubbed execution diagnostics for ADMIN only (ADR-026).
    execution_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    raw_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    project = relationship("Project", back_populates="analyses")
    executor = relationship("User", back_populates="analyses")
    findings = relationship("Finding", back_populates="analysis")
