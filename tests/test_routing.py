import pytest
from app.modules.routing.strategies import (
    GeoNode,
    NearestNeighborTSPStrategy,
    RoadNetworkAdapterTSPStrategy,
    RoutePlannerContext,
)
from app.modules.routing.adapters import OpenRouteServiceAdapter, IExternalDistancePort


def test_geonode_value_object_immutability_and_validation():
    node = GeoNode(1, "CONT-01", -12.0365, -77.0241, "Jr. Trujillo")
    assert node.container_id == 1
    assert node.code == "CONT-01"

    with pytest.raises(Exception):
        node.latitude = -12.0000

    with pytest.raises(ValueError, match="Latitud inválida"):
        GeoNode(2, "CONT-ERR", 95.0, -77.0, "Punto Inválido")

    with pytest.raises(ValueError, match="Longitud inválida"):
        GeoNode(3, "CONT-ERR", -12.0, 190.0, "Punto Inválido")


def test_nearest_neighbor_tsp_strategy_computation():
    depot = GeoNode(0, "DEPOT-RIMAC", -12.0298, -77.0285, "Cochera Municipal")
    nodes = [
        GeoNode(1, "CONT-01", -12.0365, -77.0241, "Alameda"),
        GeoNode(2, "CONT-02", -12.0392, -77.0289, "Jr. Trujillo"),
        GeoNode(3, "CONT-03", -12.0271, -77.0315, "Av. Alcázar"),
    ]
    strategy = NearestNeighborTSPStrategy()
    result = strategy.calculate_route(depot, nodes)

    assert result.algorithm == "NearestNeighborTSPStrategy"
    assert result.total_stops == 3
    assert result.total_distance_km > 0.0
    assert len(result.ordered_stops) == 3
    assert [s.sequence_order for s in result.ordered_stops] == [1, 2, 3]


def test_strategy_edge_case_empty_nodes():
    depot = GeoNode(0, "DEPOT-RIMAC", -12.0298, -77.0285, "Cochera Municipal")
    strategy = NearestNeighborTSPStrategy()
    result = strategy.calculate_route(depot, [])
    assert result.total_stops == 0
    assert result.total_distance_km == 0.0
    assert result.ordered_stops == []


def test_route_planner_context_dynamic_strategy_switch():
    depot = GeoNode(0, "DEPOT-RIMAC", -12.0298, -77.0285, "Cochera Municipal")
    nodes = [GeoNode(1, "CONT-01", -12.0365, -77.0241, "Alameda")]

    context = RoutePlannerContext(NearestNeighborTSPStrategy())
    plan_haversine = context.compute_optimal_circuit(depot, nodes)
    assert plan_haversine["algorithm"] == "NearestNeighborTSPStrategy"

    adapter = OpenRouteServiceAdapter()
    context.set_strategy(RoadNetworkAdapterTSPStrategy(adapter))
    plan_road = context.compute_optimal_circuit(depot, nodes)
    assert plan_road["algorithm"] == "RoadNetworkAdapterTSPStrategy"


def test_adapter_external_distance_port_contract():
    adapter = OpenRouteServiceAdapter(api_key="test_key")
    assert isinstance(adapter, IExternalDistancePort)
    dist = adapter.get_driving_distance_km((-12.0298, -77.0285), (-12.0365, -77.0241))
    assert dist > 0.0
