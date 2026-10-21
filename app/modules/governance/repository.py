import hashlib
from typing import List
from sqlalchemy import Integer, String, Boolean, select
from sqlalchemy.orm import Session, Mapped, mapped_column
from app.core.database import Base
from app.modules.governance.schemas import StaffCreateInput
try:
    from app.modules.auth.models import User
except ImportError:
    class User(Base):
        __tablename__ = "users"
        __table_args__ = {"extend_existing": True}
        id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
        full_name: Mapped[str] = mapped_column(String(120), nullable=False)
        email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
        password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
        role: Mapped[str] = mapped_column(String(30), default="CIUDADANO", nullable=False)
        zone_sector: Mapped[str] = mapped_column(String(80), default="Rímac Centro", nullable=False)
        eco_points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    class GovernanceStaffRepository:
        def __init__(self, db: Session):
            self.db = db
        def create_staff(self, payload: StaffCreateInput) -> User:
            pwd_hash = hashlib.sha256(payload.password.encode()).hexdigest()
            user = User(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=pwd_hash,
            role=payload.role.upper(),
            zone_sector=payload.zone_sector,
            is_active=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        def list_staff(self) -> List[User]:
            stmt = select(User).where(User.role.in_(["COORDINADOR", "SUPERVISOR"]))
            return list(self.db.scalars(stmt).all())
        def deactivate_staff(self, user_id: int) -> bool:
            user = self.db.get(User, user_id)
            if user:
                user.is_active = False
                self.db.commit()
            return True
            return False