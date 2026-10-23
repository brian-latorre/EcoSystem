from datetime import datetime
import secrets

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def generate_unique_eco_code() -> str:
    return f"ECO-2026-{secrets.token_hex(2).upper()}"


class DropAndGoRequest(Base):
    __tablename__ = "drop_and_go_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    package_code: Mapped[str] = mapped_column(
        String(25), unique=True, index=True, default=generate_unique_eco_code
    )
    citizen_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    container_code: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    material_type: Mapped[str] = mapped_column(String(40), nullable=False)
    weight_range_declared: Mapped[str] = mapped_column(String(30), nullable=False)
    zone_sector: Mapped[str] = mapped_column(
        String(80), default="Rímac Centro", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="REGISTRADA", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class CitizenAlertNotification(Base):
    __tablename__ = "citizen_alert_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    citizen_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    channel: Mapped[str] = mapped_column(
        String(40), default="PUSH_MOVIL", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
