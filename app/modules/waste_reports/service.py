from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.containers.repository import ContainerRepository
from app.modules.waste_reports.repository import WasteReportRepository
from app.modules.waste_reports.schemas import WasteReportCreate


class WasteReportError(Exception):
    pass


class WasteReportNotFound(WasteReportError):
    pass


class WasteReportAlreadyResolved(WasteReportError):
    pass


class InvalidWasteReportLocation(WasteReportError):
    pass


class WasteReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = WasteReportRepository(db)
        self.container_repo = ContainerRepository(db)

    def create_waste_report(self, payload: WasteReportCreate):
        is_valid = self.container_repo.is_within_rimac(
            payload.latitude,
            payload.longitude
        )

        if not is_valid:
            raise InvalidWasteReportLocation(
                "La ubicación debe estar dentro del Rímac"
            )

        return self.repo.create(payload)

    def list_reports(self, status_filter: Optional[str] = None) -> List:

        return self.repo.find_all(
            status_filter=status_filter
        )

    def resolve_report(self, report_id: int):
        report = self.repo.find_by_id(report_id)

        if report is None:
            raise WasteReportNotFound(
                "La denuncia no existe"
            )

        if report.status == "ATENDIDA":
            raise WasteReportAlreadyResolved(
                "La denuncia ya fue atendida"
            )

        return self.repo.update_status(
            report_id,
            "ATENDIDA"
        )