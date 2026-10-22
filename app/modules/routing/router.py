from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.modules.routing.adapters import OpenRouteServiceAdapter
from app.modules.routing.schemas import RoutePlanResponse, RoutingModeEnum
from app.modules.routing.strategies import (
    GeoNode,
    IRoutingStrategy,
    NearestNeighborTSPStrategy,
    RoadNetworkAdapterTSPStrategy,
    RoutePlannerContext,
)

router = APIRouter(
    prefix="/routes",
    tags=["Motor de Enrutamiento TSP (HU-009 / HU-010)"],
)

FALLBACK_RIMAC_NODES: List[GeoNode] = [
    GeoNode(1, "CONT-RIMAC-01", -12.0365, -77.0241, "Alameda de los Descalzos cdra. 1"),
    GeoNode(2, "CONT-RIMAC-02", -12.0392, -77.0289, "Jr. Trujillo cdra. 4"),
    GeoNode(3, "CONT-RIMAC-03", -12.0271, -77.0315, "Av. Samuel Alcázar cdra. 6"),
    GeoNode(6, "CONT-RIMAC-06", -12.0322, -77.0381, "Av. Caquetá cdra. 2"),
]


def _load_active_stops(db: Session) -> List[GeoNode]:
    try:
        from app.modules.containers.models import Container

        stmt = select(Container).where(Container.status == "LLENO")
        full_containers = list(db.scalars(stmt).all())
        nodes = [
            GeoNode(c.id, c.code, c.latitude, c.longitude, c.address)
            for c in full_containers
        ]
        if nodes:
            return nodes
    except Exception:
        db.rollback()
    return FALLBACK_RIMAC_NODES


def _resolve_strategy(mode: RoutingModeEnum, api_key: str) -> IRoutingStrategy:
    if mode == RoutingModeEnum.ROAD:
        adapter = OpenRouteServiceAdapter(api_key=api_key)
        return RoadNetworkAdapterTSPStrategy(adapter)
    return NearestNeighborTSPStrategy()


@router.get("/optimal-daily", response_model=RoutePlanResponse)
def get_daily_optimal_route(
    mode: RoutingModeEnum = Query(RoutingModeEnum.HAVERSINE),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    depot = GeoNode(
        0,
        "DEPOT-RIMAC",
        settings.MUNICIPAL_DEPOT_LAT,
        settings.MUNICIPAL_DEPOT_LON,
        "Cochera Municipal del Rímac",
    )
    stops = _load_active_stops(db)
    strategy = _resolve_strategy(mode, settings.OPENROUTESERVICE_API_KEY)
    return RoutePlannerContext(strategy).compute_optimal_circuit(depot, stops)
