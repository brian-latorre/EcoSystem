from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from app.modules.governance.repository import User


def _build_test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    User.__table__.create(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_register_and_list_operational_staff():
    client = _build_test_client()
    try:
        res_driver = client.post(
            "/api/v1/governance/staff",
            json={
                "full_name": "Carlos Rojas",
                "email": "carlos.conductor@rimac.gob.pe",
                "password": "secret123",
                "role": "CONDUCTOR",
                "zone_sector": "Rímac Centro",
            },
        )
        assert res_driver.status_code == 201
        body = res_driver.json()
        assert body["role"] == "CONDUCTOR"
        assert "password_hash" not in body

        res_operator = client.post(
            "/api/v1/governance/staff",
            json={
                "full_name": "Luis Perez",
                "email": "luis.operario@rimac.gob.pe",
                "password": "secret123",
                "role": "OPERARIO",
                "zone_sector": "Planta Rímac",
            },
        )
        assert res_operator.status_code == 201

        res_list = client.get("/api/v1/governance/staff")
        assert res_list.status_code == 200
        roles = {item["role"] for item in res_list.json()}
        assert {"CONDUCTOR", "OPERARIO"}.issubset(roles)
    finally:
        app.dependency_overrides.clear()


def test_duplicate_staff_email_returns_conflict_and_deactivate_works():
    client = _build_test_client()
    try:
        payload = {
            "full_name": "Ana Torres",
            "email": "ana.coord@rimac.gob.pe",
            "password": "secret123",
            "role": "COORDINADOR",
            "zone_sector": "Alameda",
        }
        created = client.post("/api/v1/governance/staff", json=payload)
        assert created.status_code == 201
        staff_id = created.json()["id"]

        duplicate = client.post("/api/v1/governance/staff", json=payload)
        assert duplicate.status_code == 409

        deactivated = client.delete(f"/api/v1/governance/staff/{staff_id}")
        assert deactivated.status_code == 200

        staff_list = client.get("/api/v1/governance/staff").json()
        target = next(s for s in staff_list if s["id"] == staff_id)
        assert target["is_active"] is False
    finally:
        app.dependency_overrides.clear()
