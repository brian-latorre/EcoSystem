from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.routing.repository import RoutingContainerRepository
from app.modules.routing.schemas import RoutePlanResponse, RoutingModeEnum
from app.modules.routing.service import RoutingService

router = APIRouter(
    prefix="/routes",
    tags=["Motor de Enrutamiento TSP (HU-009 / HU-010)"],
)


def get_routing_service(db: Session = Depends(get_db)) -> RoutingService:
    return RoutingService(RoutingContainerRepository(db))


@router.get("/optimal-daily", response_model=RoutePlanResponse)
def get_daily_optimal_route(
    mode: RoutingModeEnum = Query(RoutingModeEnum.HAVERSINE),
    service: RoutingService = Depends(get_routing_service),
):
    return service.compute_daily_route(mode)
