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
from app.modules.containers.models import (Container, ContainerCitizenReport, ContainerFullEvent, DistrictBoundary)
from app.modules.containers.router import router

# Base de Datos de Pruebas
settings = get_settings()

test_url = make_url(settings.DATABASE_URL).set(
    database="ecosystem_test_db"
)

if test_url.database != "ecosystem_test_db":
    raise RuntimeError(
        "Las pruebas deben utilizar ecosystem_test_db"
    )

test_engine = create_engine(
    test_url,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

TABLES = [
    DistrictBoundary.__table__,
    Container.__table__,
    ContainerCitizenReport.__table__,
    ContainerFullEvent.__table__,
]

ROOT = Path(__file__).resolve().parents[2]
GEOJSON_PATH = ROOT / "data" / "geo" / "rimac.geojson"


# Aplicación FastAPI para pruebas
test_app = FastAPI()
test_app.include_router(router, prefix="/api/v1")


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

test_app.dependency_overrides[get_db] = override_get_db


# Preparar la base de datos de pruebas antes de ejecutar los tests
@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():

    # Crear solamente las tablas de containers
    with test_engine.begin() as conn:
        conn.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS postgis"
            )
        )

    Base.metadata.create_all(
        bind=test_engine,
        tables=TABLES
    )

    # Cargar el polígono del Rímac
    with open(
        GEOJSON_PATH,
        "r",
        encoding="utf-8-sig"
    ) as file:
        data = json.load(file)

    features = data.get("features", [])

    if len(features) != 1:
        raise ValueError(
            "El GeoJSON debe tener un solo distrito"
        )

    feature = features[0]
    properties = feature["properties"]

    if properties.get("IDDIST") != "150128":
        raise ValueError(
            "El GeoJSON no corresponde al Rímac"
        )

    geometry_json = json.dumps(
        feature["geometry"]
    )

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


# Limpiar los datos de prueba antes y después de cada test
@pytest.fixture(autouse=True)
def clean_test_containers():

    # Limpieza inicial
    with test_engine.begin() as conn:
        conn.execute(
            text("""
                TRUNCATE TABLE
                    container_full_events,
                    container_citizen_reports,
                    containers
                RESTART IDENTITY CASCADE
            """)
        )

    yield

    # Limpieza final
    with test_engine.begin() as conn:
        conn.execute(
            text("""
                TRUNCATE TABLE
                    container_full_events,
                    container_citizen_reports,
                    containers
                RESTART IDENTITY CASCADE
            """)
        )

# Cliente de prueba para la API
@pytest.fixture
def client():
    with TestClient(test_app) as test_client:
        yield test_client

# Fixture para la sesión de base de datos de prueba
@pytest.fixture
def db_engine():
    return test_engine