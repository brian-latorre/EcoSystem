from datetime import datetime
from sqlalchemy import (
    Integer, String, Float, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography
from app.core.database import Base


class Container(Base):
    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    code: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(120), nullable=False
    )

    address: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    latitude: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    geom = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30), default="DISPONIBLE", nullable=False
    )

    current_reports_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    capacity_kg: Mapped[float] = mapped_column(
        Float, default=150.0, nullable=False
    )


class ContainerCitizenReport(Base):
    __tablename__ = "container_citizen_reports"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    container_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("containers.id"),
        nullable=False
    )

    citizen_id: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "container_id",
            "citizen_id",
            name="uq_container_citizen_vote"
        ),
    )
