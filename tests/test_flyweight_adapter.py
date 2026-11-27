from dataclasses import FrozenInstanceError
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.modules.containers.adapters import GeoJsonContainerAdapter
from app.modules.containers.flyweight import (
    ContainerFlyweightFactory,
    ContainerVisualFlyweight,
)
from app.modules.containers.service import ContainerThresholdService
from app.modules.drop_and_go.models import CitizenAlertNotification, DropAndGoRequest
from app.modules.drop_and_go.observers import CitizenSectorAlertObserver
from app.modules.governance.models import SystemParameterPolicy
from app.modules.plant.flyweight import MaterialFlyweightFactory, MaterialSpecFlyweight
from app.modules.routing.adapters import (
    IExternalDistancePort,
    OpenRouteServiceAdapter,
    OpenRouteServiceGeoJSONClient,
)


def test_container_flyweight_reuses_shared_instances_in_ram():
    ContainerFlyweightFactory.clear_cache()

    statuses = ["DISPONIBLE", "LLENO", "INACTIVO", " disponible ", "lleno"]
    instances = [
        ContainerFlyweightFactory.get_flyweight(statuses[i % len(statuses)])
        for i in range(1000)
    ]

    assert len(instances) == 1000
    assert ContainerFlyweightFactory.pool_size() == 3

    fw_disp_a = ContainerFlyweightFactory.get_flyweight("DISPONIBLE")
    fw_disp_b = ContainerFlyweightFactory.get_flyweight(" disponible ")
    fw_lleno = ContainerFlyweightFactory.get_flyweight("LLENO")

    assert isinstance(fw_disp_a, ContainerVisualFlyweight)
    assert fw_disp_a is fw_disp_b
    assert fw_disp_a is not fw_lleno
    assert fw_lleno.marker_color == "#e11d48"
    assert fw_lleno.dispatch_eligible is True

    with pytest.raises(FrozenInstanceError):
        fw_disp_a.marker_color = "#000000"


def test_geojson_container_adapter_transforms_coordinates_and_enriches_flyweight():
    ContainerFlyweightFactory.clear_cache()
    containers = [
        SimpleNamespace(
            id=1,
            code="CONT-01",
            name="Alameda",
            address="Jr. Trujillo",
            latitude=-12.0365,
            longitude=-77.0241,
            status="DISPONIBLE",
            capacity_kg=150.0,
            current_reports_count=1,
        ),
        SimpleNamespace(
            id=2,
            code="CONT-02",
            name="Alcazar",
            address="Av. Alcazar",
            latitude=-12.0271,
            longitude=-77.0315,
            status="LLENO",
            capacity_kg=150.0,
            current_reports_count=3,
        ),
    ]

    collection = GeoJsonContainerAdapter.to_feature_collection(containers)

    assert collection["type"] == "FeatureCollection"
    assert len(collection["features"]) == 2
    assert collection["metadata"]["total_features"] == 2
    assert collection["metadata"]["flyweight_instances_in_ram"] == 2

    first = collection["features"][0]
    second = collection["features"][1]
    assert first["geometry"]["coordinates"] == [-77.0241, -12.0365]
    assert first["properties"]["marker_color"] == "#059669"
    assert second["geometry"]["coordinates"] == [-77.0315, -12.0271]
    assert second["properties"]["marker_color"] == "#e11d48"
    assert second["properties"]["dispatch_eligible"] is True


def test_material_flyweight_reuses_shared_specs_in_ram():
    MaterialFlyweightFactory.clear_cache()

    p1 = MaterialFlyweightFactory.get_spec("plastico")
    p2 = MaterialFlyweightFactory.get_spec(" PLASTICO ")
    paper = MaterialFlyweightFactory.get_spec("PAPEL")
    glass = MaterialFlyweightFactory.get_spec("VIDRIO")
    metal = MaterialFlyweightFactory.get_spec("METAL")

    assert isinstance(p1, MaterialSpecFlyweight)
    assert p1 is p2
    assert MaterialFlyweightFactory.pool_size() == 4
    assert (p1.default_points_per_kg, p1.default_co2_per_kg) == (5, 1.45)
    assert paper.default_points_per_kg == 3
    assert glass.default_points_per_kg == 2
    assert metal.default_points_per_kg == 8


def test_openrouteservice_adapter_translates_lat_lon_and_meters_from_adaptee():
    client = OpenRouteServiceGeoJSONClient()
    raw = client.fetch_route_metrics([-77.0285, -12.0298], [-77.0241, -12.0365])
    assert raw["metadata"]["coordinate_order"] == "lon_lat"
    assert raw["routes"][0]["summary"]["distance"] > 0

    recorded = {}

    class FakeGeoJSONClient:
        def fetch_route_metrics(self, origin_lon_lat, destination_lon_lat):
            recorded["origin"] = origin_lon_lat
            recorded["destination"] = destination_lon_lat
            return {"routes": [{"summary": {"distance": 1250.0, "duration": 150.0}}]}

    adapter = OpenRouteServiceAdapter(client=FakeGeoJSONClient())
    assert isinstance(adapter, IExternalDistancePort)
    km = adapter.get_driving_distance_km((-12.03, -77.02), (-12.04, -77.03))

    assert recorded["origin"] == [-77.02, -12.03]
    assert recorded["destination"] == [-77.03, -12.04]
    assert km == 1.25


def test_container_threshold_service_reads_dynamic_governance_policy():
    bare_engine = create_engine("sqlite:///:memory:")
    BareSession = sessionmaker(bind=bare_engine)
    with BareSession() as bare_db:
        assert ContainerThresholdService(bare_db)._resolve_report_threshold() == 3

    engine = create_engine("sqlite:///:memory:")
    SystemParameterPolicy.__table__.create(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        assert ContainerThresholdService(db)._resolve_report_threshold() == 3
        db.add(
            SystemParameterPolicy(
                param_key="DEFAULT_CONTAINER_REPORT_THRESHOLD",
                param_value=5.0,
                unit="reportes",
                description="Umbral dinamico de prueba",
            )
        )
        db.commit()
        assert ContainerThresholdService(db)._resolve_report_threshold() == 5


def test_citizen_sector_observer_matches_sectors_ignoring_accents():
    engine = create_engine("sqlite:///:memory:")
    DropAndGoRequest.__table__.create(bind=engine)
    CitizenAlertNotification.__table__.create(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        db.add(
            DropAndGoRequest(
                citizen_id=7,
                container_code="CONT-01",
                material_type="PLASTICO",
                weight_range_declared="0-5kg",
                zone_sector="Rimac Centro",
                status="REGISTRADA",
            )
        )
        db.commit()

        observer = CitizenSectorAlertObserver()
        observer.update(
            db,
            {"event_type": "TRUCK_ARRIVING_SECTOR", "zone_sector": "Rímac Centro"},
        )
        db.commit()

        alerts = db.query(CitizenAlertNotification).all()
        assert len(alerts) == 1
        assert alerts[0].citizen_id == 7


def test_flyweight_restful_endpoints_contract():
    client = TestClient(app)

    containers_res = client.get("/api/v1/containers/flyweight-specs")
    assert containers_res.status_code == 200
    containers_data = containers_res.json()
    assert containers_data["pattern"] == "Flyweight"
    assert containers_data["pool_size"] >= 3
    assert len(containers_data["specs"]) == 3

    plant_res = client.get("/api/v1/plant/material-specs")
    assert plant_res.status_code == 200
    plant_data = plant_res.json()
    assert plant_data["pattern"] == "Flyweight"
    assert plant_data["pool_size"] >= 4
    assert len(plant_data["specs"]) == 4
