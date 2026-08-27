from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KisaCatalog(Base):
    __tablename__ = "kisa_catalog"

    kisa_code: Mapped[str] = mapped_column(String, primary_key=True)
    # E1-06 finalizes the full catalog field set; added here only because
    # Finding (E1-05, ADR-005/ADR-007) needs a source to snapshot from.
    criterion_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_severity: Mapped[str] = mapped_column(String, nullable=False)
    implementation_status: Mapped[str] = mapped_column(
        String, nullable=False, default="미구현"
    )  # 구현/미구현
    semgrep_rule_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    findings = relationship("Finding", back_populates="kisa_item")
