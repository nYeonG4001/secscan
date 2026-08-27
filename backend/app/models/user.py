from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'USER')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="USER")  # ADMIN or USER
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    projects_created = relationship(
        "Project", back_populates="creator", foreign_keys="Project.created_by"
    )
    project_accesses = relationship(
        "ProjectAccess", back_populates="user", foreign_keys="ProjectAccess.user_id"
    )
    analyses = relationship("Analysis", back_populates="executor")
