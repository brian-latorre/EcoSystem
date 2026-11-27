from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.waste_reports.schemas import (WasteReportCreate, WasteReportResponse)
from app.modules.waste_reports.service import (WasteReportService, WasteReportNotFound,
    WasteReportAlreadyResolved,InvalidWasteReportLocation)

router = APIRouter(
    prefix="/waste-reports",
    tags=["Waste Reports"]
)

def get_waste_report_service(db: Session = Depends(get_db)) -> WasteReportService:
    return WasteReportService(db)

@router.post("/",
    response_model=WasteReportResponse,
    status_code=201
)

def create_report(
    payload: WasteReportCreate,
    service: WasteReportService = Depends(
        get_waste_report_service
    )
):
    try:
        return service.create_waste_report(payload)

    except InvalidWasteReportLocation as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc

@router.get("/pending",
    response_model=List[WasteReportResponse]
)

def get_pending_reports(
    service: WasteReportService = Depends(
        get_waste_report_service
    )
):
    return service.list_reports(
        status_filter="PENDIENTE"
    )

@router.patch("/{report_id}/resolve",
    response_model=WasteReportResponse
)

def resolve_report(
    report_id: int,
    service: WasteReportService = Depends(
        get_waste_report_service
    )
):
    try:
        return service.resolve_report(report_id)

    except WasteReportNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc

    except WasteReportAlreadyResolved as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc)
        ) from exc