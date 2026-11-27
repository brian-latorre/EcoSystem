from typing import Any, Dict, List
from app.core.config import get_settings
from app.modules.routing.adapters import OpenRouteServiceAdapter
from app.modules.routing.repository import RoutingContainerRepository
from app.modules.routing.schemas import RoutingModeEnum
from app.modules.routing.strategies import (
    GeoNode,
    IRoutingStrategy,
    NearestNeighborTSPStrategy,
    RoadNetworkAdapterTSPStrategy,
    RoutePlannerContext,
    TwoOptTSPStrategy,
)


FALLBACK_RIMAC_NODES: List[GeoNode] = [
    GeoNode(1, "CONT-RIMAC-01", -12.0365, -77.0241, "Alameda de los Descalzos cdra. 1"),
    GeoNode(2, "CONT-RIMAC-02", -12.0392, -77.0289, "Jr. Trujillo cdra. 4"),
    GeoNode(3, "CONT-RIMAC-03", -12.0271, -77.0315, "Av. Samuel Alcázar cdra. 6"),
    GeoNode(6, "CONT-RIMAC-06", -12.0322, -77.0381, "Av. Caquetá cdra. 2"),
]


class RoutingService:
    def __init__(self, repository: RoutingContainerRepository):
        self._repository = repository
        self._settings = get_settings()

    def _resolve_strategy(self, mode: RoutingModeEnum) -> IRoutingStrategy:
        if mode == RoutingModeEnum.ROAD:
            adapter = OpenRouteServiceAdapter(api_key=self._settings.OPENROUTESERVICE_API_KEY)
            return RoadNetworkAdapterTSPStrategy(adapter)
        if mode == RoutingModeEnum.TWO_OPT:
            return TwoOptTSPStrategy()
        return NearestNeighborTSPStrategy()

    def compute_daily_route(self, mode: RoutingModeEnum) -> Dict[str, Any]:
        depot = GeoNode(
            0,
            "DEPOT-RIMAC",
            self._settings.MUNICIPAL_DEPOT_LAT,
            self._settings.MUNICIPAL_DEPOT_LON,
            "Cochera Municipal del Rímac",
        )
        stops = self._repository.get_full_stops_or_fallback(FALLBACK_RIMAC_NODES)
        strategy = self._resolve_strategy(mode)
        return RoutePlannerContext(strategy).compute_optimal_circuit(depot, stops)
