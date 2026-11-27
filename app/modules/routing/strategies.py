from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import math
from typing import List, Dict, Any, Callable
from app.modules.routing.adapters import IExternalDistancePort


@dataclass(frozen=True)
class GeoNode:
    container_id: int
    code: str
    latitude: float
    longitude: float
    address: str

    def __post_init__(self):
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitud inválida: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitud inválida: {self.longitude}")


@dataclass(frozen=True)
class RouteStop:
    sequence_order: int
    container_id: int
    container_code: str
    address: str
    latitude: float
    longitude: float
    leg_distance_km: float
    estimated_arrival_min: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoutePlan:
    algorithm: str
    total_stops: int
    total_distance_km: float
    estimated_total_minutes: float
    ordered_stops: List[RouteStop]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "total_stops": self.total_stops,
            "total_distance_km": self.total_distance_km,
            "estimated_total_minutes": self.estimated_total_minutes,
            "ordered_stops": [s.to_dict() for s in self.ordered_stops],
        }


class IRoutingStrategy(ABC):
    @abstractmethod
    def calculate_route(self, depot: GeoNode, stops: List[GeoNode]) -> RoutePlan:
        pass


def _build_route_plan(
    depot: GeoNode,
    ordered_nodes: List[GeoNode],
    distance_metric: Callable[[GeoNode, GeoNode], float],
    algorithm: str,
    speed: float,
) -> RoutePlan:
    if not ordered_nodes:
        return RoutePlan(algorithm, 0, 0.0, 0.0, [])

    ordered_stops: List[RouteStop] = []
    current = depot
    total_km = 0.0

    for step, node in enumerate(ordered_nodes, start=1):
        leg_km = distance_metric(current, node)
        total_km += leg_km
        ordered_stops.append(
            RouteStop(
                step,
                node.container_id,
                node.code,
                node.address,
                node.latitude,
                node.longitude,
                round(leg_km, 2),
                round((total_km / speed) * 60, 1),
            )
        )
        current = node

    return RoutePlan(
        algorithm,
        len(ordered_stops),
        round(total_km, 2),
        round((total_km / speed) * 60, 1),
        ordered_stops,
    )


def _nearest_neighbor_order(
    depot: GeoNode,
    stops: List[GeoNode],
    distance_metric: Callable[[GeoNode, GeoNode], float],
) -> List[GeoNode]:
    unvisited = list(stops)
    ordered: List[GeoNode] = []
    current = depot

    while unvisited:
        nearest = min(unvisited, key=lambda node: distance_metric(current, node))
        ordered.append(nearest)
        current = nearest
        unvisited.remove(nearest)

    return ordered


def _solve_circuit(
    depot: GeoNode,
    stops: List[GeoNode],
    distance_metric: Callable[[GeoNode, GeoNode], float],
    algorithm: str,
    speed: float,
) -> RoutePlan:
    ordered_nodes = _nearest_neighbor_order(depot, stops, distance_metric)
    return _build_route_plan(depot, ordered_nodes, distance_metric, algorithm, speed)


class NearestNeighborTSPStrategy(IRoutingStrategy):
    speed_kmh: float = 22.0

    @staticmethod
    def _distance(p1: GeoNode, p2: GeoNode) -> float:
        d_lat = math.radians(p2.latitude - p1.latitude)
        d_lon = math.radians(p2.longitude - p1.longitude)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(p1.latitude))
            * math.cos(math.radians(p2.latitude))
            * math.sin(d_lon / 2) ** 2
        )
        return round(2 * 6371.0 * math.asin(math.sqrt(a)), 3)

    def calculate_route(self, depot: GeoNode, stops: List[GeoNode]) -> RoutePlan:
        return _solve_circuit(
            depot, stops, self._distance, "NearestNeighborTSPStrategy", self.speed_kmh
        )


class TwoOptTSPStrategy(IRoutingStrategy):
    speed_kmh: float = 22.0

    def _path_distance(self, depot: GeoNode, route: List[GeoNode]) -> float:
        if not route:
            return 0.0
        total = NearestNeighborTSPStrategy._distance(depot, route[0])
        for idx in range(len(route) - 1):
            total += NearestNeighborTSPStrategy._distance(route[idx], route[idx + 1])
        return total

    def calculate_route(self, depot: GeoNode, stops: List[GeoNode]) -> RoutePlan:
        metric = NearestNeighborTSPStrategy._distance
        best = _nearest_neighbor_order(depot, stops, metric)
        if len(best) < 3:
            return _build_route_plan(depot, best, metric, "TwoOptTSPStrategy", self.speed_kmh)

        best_dist = self._path_distance(depot, best)
        improved = True
        while improved:
            improved = False
            for i in range(len(best) - 1):
                for j in range(i + 1, len(best)):
                    candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                    cand_dist = self._path_distance(depot, candidate)
                    if cand_dist + 1e-6 < best_dist:
                        best = candidate
                        best_dist = cand_dist
                        improved = True

        return _build_route_plan(depot, best, metric, "TwoOptTSPStrategy", self.speed_kmh)


class RoadNetworkAdapterTSPStrategy(IRoutingStrategy):
    speed_kmh: float = 20.0

    def __init__(self, adapter: IExternalDistancePort):
        self._adapter = adapter

    def calculate_route(self, depot: GeoNode, stops: List[GeoNode]) -> RoutePlan:
        def road_distance(p1: GeoNode, p2: GeoNode) -> float:
            return self._adapter.get_driving_distance_km(
                (p1.latitude, p1.longitude), (p2.latitude, p2.longitude)
            )

        return _solve_circuit(
            depot, stops, road_distance, "RoadNetworkAdapterTSPStrategy", self.speed_kmh
        )


class RoutePlannerContext:
    def __init__(self, strategy: IRoutingStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: IRoutingStrategy) -> None:
        self._strategy = strategy

    def compute_optimal_circuit(
        self, depot: GeoNode, containers: List[GeoNode]
    ) -> Dict[str, Any]:
        return self._strategy.calculate_route(depot, containers).to_dict()
