from pydantic import BaseModel, Field
class ParameterUpdateInput(BaseModel):
    param_value: float
    description: str
class MultiplierCreateInput(BaseModel):
    material_type: str = Field(... , examples=["PLASTICO"])
    points_per_kg: int = Field(... , examples=[5])
    co2_saved_per_kg: float = Field(1.45, examples=[1.45])
class StaffCreateInput(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = Field(... , examples=["COORDINADOR", "SUPERVISOR"])
    zone_sector: str = "Rímac Centro"
