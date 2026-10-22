from enum import Enum
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class UserRole(str, Enum):
    CIUDADANO = "CIUDADANO"
    CONDUCTOR = "CONDUCTOR"
    OPERARIO = "OPERARIO"
    ADMIN = "ADMIN"
    COORDINADOR = "COORDINADOR"
    SUPERVISOR = "SUPERVISOR"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.CIUDADANO, nullable=False)
    zone_sector: Mapped[str] = mapped_column(String(30), default="Rimac Centro", nullable=False)
    eco_points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)