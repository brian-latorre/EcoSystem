import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.modules.containers.models import DistrictBoundary
from app.modules.waste_reports.models import AbandonedWasteReport
from app.modules.waste_reports.router import router as waste_router

# Configurar la base de datos aislada
settings = get_settings()

test_url = make_url(settings.DATABASE_URL).set(
    database="ecosystem_test_db"
)

if test_url.database != "ecosystem_test_db":
    raise RuntimeError("Base de datos de pruebas incorrecta")

test_engine = create_engine(
    test_url,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

# Crear aplicación independiente para pruebas
api_app = FastAPI()
api_app.include_router(
    waste_router,
    prefix="/api/v1"
)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

api_app.dependency_overrides[get_db] = override_get_db

# Preparar PostGIS y el distrito del Rímac
@pytest.fixture(scope="module", autouse=True)
def prepare_database():
    with test_engine.begin() as conn:
        conn.execute(
            text("CREATE EXTENSION IF NOT EXISTS postgis")
        )

    Base.metadata.create_all(
        bind=test_engine,
        tables=[
            DistrictBoundary.__table__,
            AbandonedWasteReport.__table__
        ]
    )

    root = Path(__file__).resolve().parents[1]
    geojson_path = root / "data" / "geo" / "rimac.geojson"

    with open(geojson_path, encoding="utf-8-sig") as file:
        geojson = json.load(file)

    features = geojson.get("features", [])

    if len(features) != 1:
        raise ValueError("GeoJSON del Rímac inválido")

    feature = features[0]

    if feature["properties"].get("IDDIST") != "150128":
        raise ValueError("El GeoJSON no corresponde al Rímac")

    geometry_json = json.dumps(feature["geometry"])

    with test_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO district_boundaries
                    (ubigeo, name, geom)
                VALUES (
                    '150128',
                    'RIMAC',
                    ST_Multi(
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:geometry),
                            4326
                        )
                    )
                )
                ON CONFLICT (ubigeo)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    geom = EXCLUDED.geom
            """),
            {"geometry": geometry_json}
        )

    yield
    test_engine.dispose()

# Aislar los registros entre pruebas
@pytest.fixture(autouse=True)
def clean_waste_reports():
    with test_engine.begin() as conn:
        conn.execute(
            text("""
                TRUNCATE TABLE abandoned_waste_reports
                RESTART IDENTITY CASCADE
            """)
        )

    yield

    with test_engine.begin() as conn:
        conn.execute(
            text("""
                TRUNCATE TABLE abandoned_waste_reports
                RESTART IDENTITY CASCADE
            """)
        )

@pytest.fixture
def client():
    with TestClient(api_app) as test_client:
        yield test_client


@pytest.fixture
def sample_report():
    return {
        "citizen_id": 101,
        "description": "Bolsas de basura abandonadas",
        "photo_evidence_url": "/static/uploads/prueba.jpg",
        "address_reference": "Rímac, Lima",
        "latitude": -12.0251,
        "longitude": -77.0312
    }

# TEST 1: Crear denuncia
def test_create_waste_report(client, sample_report):
    response = client.post(
        "/api/v1/waste-reports/",
        json=sample_report
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["id"] > 0
    assert data["status"] == "PENDIENTE"
    assert data["description"] == sample_report["description"]

# TEST 2: Listar denuncias pendientes
def test_list_pending_reports(client, sample_report):
    create_response = client.post(
        "/api/v1/waste-reports/",
        json=sample_report
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/waste-reports/pending"
    )

    assert response.status_code == 200

    reports = response.json()

    assert len(reports) == 1
    assert reports[0]["status"] == "PENDIENTE"

# TEST 3: Resolver una denuncia
def test_resolve_waste_report(client, sample_report):
    create_response = client.post(
        "/api/v1/waste-reports/",
        json=sample_report
    )

    assert create_response.status_code == 201

    report_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/waste-reports/{report_id}/resolve"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ATENDIDA"

# TEST 4: Una denuncia atendida deja de estar pendiente
def test_resolved_report_not_pending(client, sample_report):
    create_response = client.post(
        "/api/v1/waste-reports/",
        json=sample_report
    )

    assert create_response.status_code == 201

    report_id = create_response.json()["id"]

    resolve_response = client.patch(
        f"/api/v1/waste-reports/{report_id}/resolve"
    )

    assert resolve_response.status_code == 200

    pending_response = client.get(
        "/api/v1/waste-reports/pending"
    )

    assert pending_response.status_code == 200

    pending_ids = [
        report["id"]
        for report in pending_response.json()
    ]

    assert report_id not in pending_ids