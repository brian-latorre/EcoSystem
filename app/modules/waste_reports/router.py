from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.modules.waste_reports.schemas import WasteReportCreate, WasteReportResponse
from app.modules.waste_reports.repository import WasteReportRepository

router = APIRouter(prefix="/waste-reports", tags=["Waste Reports"])

@router.post("/", response_model=WasteReportResponse)
def create_report(payload: WasteReportCreate, db: Session = Depends(get_db)):
    repo = WasteReportRepository(db)
    return repo.create(payload)

@router.get("/pending", response_model=List[WasteReportResponse])
def get_pending_reports(db: Session = Depends(get_db)):
    repo = WasteReportRepository(db)
    return repo.get_pending()