from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KisaRuleMapping(Base):
    __tablename__ = "kisa_rule_mapping"
    __table_args__ = (
        UniqueConstraint("engine", "engine_rule_id", name="uq_kisa_rule_mapping_engine_rule"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engine: Mapped[str] = mapped_column(String, nullable=False)
    engine_rule_id: Mapped[str] = mapped_column(String, nullable=False)
    kisa_code: Mapped[str] = mapped_column(
        String, ForeignKey("kisa_catalog.kisa_code"), nullable=False
    )

    kisa_item = relationship("KisaCatalog")
