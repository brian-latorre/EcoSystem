from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from app.modules.waste_reports.models import AbandonedWasteReport
from app.modules.waste_reports.schemas import WasteReportCreate

class WasteReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: WasteReportCreate) -> AbandonedWasteReport:
        wkt_point = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)

        entity = AbandonedWasteReport(
            citizen_id=payload.citizen_id,
            description=payload.description,
            photo_evidence_url=payload.photo_evidence_url,
            address_reference=payload.address_reference,
            latitude=payload.latitude,
            longitude=payload.longitude,
            geom=wkt_point,
            status="PENDIENTE"
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def find_all(self, status_filter: Optional[str] = None) -> List[AbandonedWasteReport]:
        stmt = select(AbandonedWasteReport)

        if status_filter is not None:
            stmt = stmt.where(AbandonedWasteReport.status == status_filter)

        stmt = stmt.order_by(AbandonedWasteReport.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_pending(self) -> List[AbandonedWasteReport]:
        return self.find_all(status_filter="PENDIENTE")

    def find_by_id(self, report_id: int) -> Optional[AbandonedWasteReport]:
        return self.db.get(AbandonedWasteReport, report_id)

    def update_status(self, report_id: int, status: str) -> Optional[AbandonedWasteReport]:
        entity = self.find_by_id(report_id)
        if entity is None:
            return None
        entity.status = status
        self.db.commit()
        self.db.refresh(entity)
        return entity