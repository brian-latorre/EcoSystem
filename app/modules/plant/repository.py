from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.auth.models import User
from app.modules.drop_and_go.models import DropAndGoRequest
from app.modules.governance.models import MaterialPointMultiplier
from app.modules.plant.models import PlantProcessingRecord


DEFAULT_MATERIAL_RATES = {
    "PLASTICO": (5, 1.45),
    "PAPEL": (3, 0.95),
    "VIDRIO": (2, 0.30),
    "METAL": (8, 2.10),
}


class PlantRepository:
    def __init__(self, db: Session):
        self._db = db

    @staticmethod
    def _normalize_code(package_code: str) -> str:
        return package_code.strip().lstrip("#").upper()

    def find_package_by_code(self, package_code: str) -> Optional[DropAndGoRequest]:
        normalized = self._normalize_code(package_code)
        stmt = select(DropAndGoRequest).where(DropAndGoRequest.package_code == normalized)
        return self._db.scalar(stmt)

    def list_pending_packages(self) -> List[DropAndGoRequest]:
        stmt = (
            select(DropAndGoRequest)
            .where(DropAndGoRequest.status.in_(["REGISTRADA", "RECOLECTADA"]))
            .order_by(DropAndGoRequest.created_at.desc())
        )
        return list(self._db.scalars(stmt).all())

    def get_material_multiplier(self, material_type: str) -> Tuple[int, float]:
        mat_key = material_type.strip().upper()
        stmt = select(MaterialPointMultiplier).where(
            MaterialPointMultiplier.material_type == mat_key,
            MaterialPointMultiplier.is_active.is_(True),
        )
        record = self._db.scalar(stmt)
        if record:
            return record.points_per_kg, record.co2_saved_per_kg
        return DEFAULT_MATERIAL_RATES.get(mat_key, (3, 1.0))

    def save_processing(
        self,
        record: PlantProcessingRecord,
        package: DropAndGoRequest,
        points_awarded: int,
    ) -> tuple[PlantProcessingRecord, int]:
        package.status = "PROCESADO_EN_PLANTA"
        self._db.add(record)

        new_balance = 0
        citizen = self._db.get(User, package.citizen_id)
        if citizen:
            citizen.eco_points_balance += points_awarded
            new_balance = citizen.eco_points_balance

        self._db.commit()
        self._db.refresh(record)
        return record, new_balance

    def list_recent_records(self, limit: int = 20) -> List[PlantProcessingRecord]:
        stmt = (
            select(PlantProcessingRecord)
            .order_by(PlantProcessingRecord.processed_at.desc())
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())
