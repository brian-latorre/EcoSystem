from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography
from app.core.database import Base

class AbandonedWasteReport(Base):
    __tablename__ = "abandoned_waste_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    citizen_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    photo_evidence_url: Mapped[str] = mapped_column(String(300), nullable=False)
    address_reference: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDIENTE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)