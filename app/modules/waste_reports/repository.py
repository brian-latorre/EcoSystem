from typing import List
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

    def get_pending(self) -> List[AbandonedWasteReport]:
        stmt = select(AbandonedWasteReport).where(AbandonedWasteReport.status == "PENDIENTE").order_by(AbandonedWasteReport.created_at.desc())
        return list(self.db.scalars(stmt).all())