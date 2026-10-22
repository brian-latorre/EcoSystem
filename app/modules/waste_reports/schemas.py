from datetime import datetime
from pydantic import BaseModel, Field

class WasteReportCreate(BaseModel):
    citizen_id: int
    description: str = Field(..., examples=["Acumulación de desmonte y bolsas rotas"])
    photo_evidence_url: str = Field(..., examples=["/static/uploads/denuncia_rimac_01.jpg"])
    address_reference: str = Field(..., examples=["Cruce Av. Alcázar con Jr. Tarapacá"])
    latitude: float = Field(..., ge=-90.0, le=90.0, examples=[-12.0251])
    longitude: float = Field(..., ge=-180.0, le=180.0, examples=[-77.0312])

class WasteReportResponse(BaseModel):
    id: int
    citizen_id: int
    description: str
    photo_evidence_url: str
    address_reference: str
    latitude: float
    longitude: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True