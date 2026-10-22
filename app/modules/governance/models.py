from sqlalchemy import Integer, String, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
class SystemParameterPolicy(Base):
    __tablename__ = "system_parameter_policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    param_key: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    param_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="unidades", nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
class MaterialPointMultiplier(Base):
    __tablename__ = "material_point_multipliers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    material_type: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    points_per_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    co2_saved_per_kg: Mapped[float] = mapped_column(Float, default=1.45, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
