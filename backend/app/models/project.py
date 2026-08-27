from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("name", name="uq_projects_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ADR-006: MVP source type is file upload; system-populated after source upload (E3).
    source_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Auto-identified by the system from the uploaded source (ADR-006); not user input.
    target_languages: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    source_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    creator = relationship("User", back_populates="projects_created", foreign_keys=[created_by])
    accesses = relationship("ProjectAccess", back_populates="project")
    analyses = relationship("Analysis", back_populates="project")


class ProjectAccess(Base):
    __tablename__ = "project_accesses"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    granted_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    project = relationship("Project", back_populates="accesses")
    user = relationship("User", back_populates="project_accesses", foreign_keys=[user_id])
    grantor = relationship("User", foreign_keys=[granted_by])
