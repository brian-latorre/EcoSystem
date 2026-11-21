from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PlantPackageLookupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    package_code: str
    citizen_id: int
    container_code: str
    material_type: str
    weight_range_declared: str
    zone_sector: str
    status: str


class PlantProcessInput(BaseModel):
    verified_weight_kg: float = Field(..., ge=0.0, le=500.0)
    verified_material: str = Field(..., min_length=1, max_length=40)
    is_contaminated: bool = False
    operator_id: int = Field(1, gt=0)
    observations: str = Field("", max_length=250)


class PlantProcessResponse(BaseModel):
    package_code: str
    citizen_id: int
    verified_material: str
    verified_weight_kg: float
    is_contaminated: bool
    points_awarded: int
    co2_saved_kg: float
    package_status: str
    citizen_new_balance: int
    evaluator_used: str
    processed_at: datetime


class PlantHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    package_code: str
    citizen_id: int
    verified_material: str
    verified_weight_kg: float
    points_awarded: int
    co2_saved_kg: float
    is_contaminated: bool
    observations: str
    processed_at: datetime
