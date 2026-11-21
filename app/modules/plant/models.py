from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PlantProcessingRecord(Base):
    __tablename__ = "plant_processing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    package_code: Mapped[str] = mapped_column(String(25), unique=True, index=True, nullable=False)
    citizen_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    operator_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    declared_material: Mapped[str] = mapped_column(String(40), nullable=False)
    verified_material: Mapped[str] = mapped_column(String(40), nullable=False)
    verified_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    co2_saved_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_contaminated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    observations: Mapped[str] = mapped_column(String(250), default="", nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
