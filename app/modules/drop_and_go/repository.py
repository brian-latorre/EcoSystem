
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.modules.drop_and_go.models import DropAndGoRequest
from app.modules.drop_and_go.schemas import DropAndGoCreateInput


class DropAndGoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: DropAndGoCreateInput) -> DropAndGoRequest:
        entity = DropAndGoRequest(
            citizen_id=payload.citizen_id,
            container_code=payload.container_code,
            material_type=payload.material_type.upper(),
            weight_range_declared=payload.weight_range_declared,
            zone_sector=payload.zone_sector,
            status="REGISTRADA"
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        return entity

    def get_by_citizen(self, citizen_id: int) -> List[DropAndGoRequest]:
        stmt = (
            select(DropAndGoRequest)
            .where(DropAndGoRequest.citizen_id == citizen_id)
            .order_by(DropAndGoRequest.created_at.desc())
        )

        return list(self.db.scalars(stmt).all())
