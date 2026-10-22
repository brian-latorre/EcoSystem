from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class RoutingModeEnum(str, Enum):
    HAVERSINE = "haversine"
    ROAD = "road"


class RouteStopResponse(BaseModel):
    sequence_order: int = Field(..., description="Orden secuencial de visita")
    container_id: int = Field(..., description="Identificador único del contenedor")
    container_code: str = Field(..., description="Código patrimonial del contenedor")
    address: str = Field(..., description="Dirección física o referencia del punto")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitud en WGS84")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitud en WGS84")
    leg_distance_km: float = Field(..., ge=0.0, description="Distancia del tramo actual en km")
    estimated_arrival_min: float = Field(..., ge=0.0, description="Tiempo acumulado estimado en minutos")


class RoutePlanResponse(BaseModel):
    algorithm: str = Field(..., description="Estrategia algorítmica GoF ejecutada")
    total_stops: int = Field(..., ge=0, description="Cantidad total de contenedores visitados")
    total_distance_km: float = Field(..., ge=0.0, description="Distancia total recorrida del circuito en km")
    estimated_total_minutes: float = Field(..., ge=0.0, description="Duración estimada del recorrido en minutos")
    ordered_stops: List[RouteStopResponse] = Field(
        default_factory=list, description="Lista secuencial de paradas"
    )
