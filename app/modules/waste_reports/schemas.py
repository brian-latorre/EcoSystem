from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal

class WasteReportCreate(BaseModel):
    citizen_id: int = Field(
        ..., gt=0
        )
    description: str = Field(
        ..., min_length=1, max_length=250
        )
    photo_evidence_url: str = Field(
        ..., min_length=1
        )
    address_reference: str = Field(
        ..., min_length=1, max_length=200
        )
    latitude: float = Field(
        ..., ge=-90.0, le=90.0
        )
    longitude: float = Field(
        ..., ge=-180.0, le=180.0
        )

class WasteReportStatusUpdate(BaseModel):
    status: Literal["PENDIENTE", "ATENDIDA"]

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

    model_config = {
        "from_attributes": True
        }