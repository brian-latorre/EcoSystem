from pydantic import BaseModel, Field


class ContainerCreate(BaseModel):
    code: str = Field(
        ..., examples=["CONT-RIMAC-01"]
    )

    name: str = Field(
        ..., examples=["Acopio Alameda de los Descalzos"]
    )

    address: str = Field(
        ..., examples=["Jr. Atahualpa cdra. 2, Rímac"]
    )

    latitude: float = Field(
        ..., ge=-90.0, le=90.0, examples=[-12.0365]
    )

    longitude: float = Field(
        ..., ge=-180.0, le=180.0, examples=[-77.0241]
    )

    capacity_kg: float = 150.0


class ContainerResponse(BaseModel):
    id: int
    code: str
    name: str
    address: str
    latitude: float
    longitude: float
    status: str
    current_reports_count: int
    capacity_kg: float

    class Config:
        from_attributes = True
