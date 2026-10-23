from datetime import datetime

from pydantic import BaseModel, Field


class DropAndGoCreateInput(BaseModel):
    citizen_id: int
    container_code: str = Field(..., examples=["CONT-RIMAC-01"])
    material_type: str = Field(..., examples=["PLASTICO"])
    weight_range_declared: str = Field(..., examples=["5-10kg"])
    zone_sector: str = Field("Rímac Centro", examples=["Rímac Centro"])


class DropAndGoResponse(BaseModel):
    id: int
    package_code: str
    citizen_id: int
    container_code: str
    material_type: str
    weight_range_declared: str
    zone_sector: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
