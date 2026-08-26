from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="USER")  # ADMIN or USER

    projects_created = relationship(
        "Project", back_populates="creator", foreign_keys="Project.created_by"
    )
    project_accesses = relationship(
        "ProjectAccess", back_populates="user", foreign_keys="ProjectAccess.user_id"
    )
    analyses = relationship("Analysis", back_populates="executor")
