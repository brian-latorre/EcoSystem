from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import get_db
from app.main import app
from app.modules.auth.models import User, UserRole
from app.modules.drop_and_go.models import DropAndGoRequest
from app.modules.governance.models import MaterialPointMultiplier
from app.modules.plant.evaluators import (
    ContaminatedRejectedEvaluator,
    MaterialEvaluatorFactory,
    RecyclableMaterialEvaluator,
)
from app.modules.plant.models import PlantProcessingRecord


def _setup_in_memory_plant():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    for table in (
        User.__table__,
        DropAndGoRequest.__table__,
        MaterialPointMultiplier.__table__,
        PlantProcessingRecord.__table__,
    ):
        table.create(bind=engine)

    db = TestingSession()
    citizen = User(
        full_name="Maria Lopez",
        email="maria@rimac.pe",
        password_hash="hash",
        role=UserRole.CIUDADANO,
        zone_sector="Rimac Centro",
        eco_points_balance=10,
    )
    db.add(citizen)
    db.add(MaterialPointMultiplier(material_type="PLASTICO", points_per_kg=6, co2_saved_per_kg=1.5))
    db.flush()
    pkg = DropAndGoRequest(
        package_code="ECO-2026-AB12",
        citizen_id=citizen.id,
        container_code="CONT-RIMAC-01",
        material_type="PLASTICO",
        weight_range_declared="1-5kg",
        zone_sector="Rimac Centro",
        status="RECOLECTADA",
    )
    db.add(pkg)
    db.commit()
    citizen_id = citizen.id
    db.close()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), citizen_id


def test_material_evaluator_factory_returns_expected_strategies():
    recyclable = MaterialEvaluatorFactory.create(False, "PLASTICO")
    assert isinstance(recyclable, RecyclableMaterialEvaluator)
    assert recyclable.evaluate(2.5, 6) == 15

    contaminated = MaterialEvaluatorFactory.create(True, "PLASTICO")
    assert isinstance(contaminated, ContaminatedRejectedEvaluator)
    assert contaminated.evaluate(5.0, 6) == 0


def test_plant_lookup_process_and_credit_points():
    client, citizen_id = _setup_in_memory_plant()
    try:
        lookup = client.get("/api/v1/plant/packages/%23ECO-2026-AB12")
        assert lookup.status_code == 200
        assert lookup.json()["citizen_id"] == citizen_id

        processed = client.post(
            "/api/v1/plant/packages/ECO-2026-AB12/process",
            json={
                "verified_weight_kg": 2.5,
                "verified_material": "PLASTICO",
                "is_contaminated": False,
                "operator_id": 1,
                "observations": "Limpio",
            },
        )
        assert processed.status_code == 200
        data = processed.json()
        assert data["points_awarded"] == 15
        assert data["citizen_new_balance"] == 25
        assert data["package_status"] == "PROCESADO_EN_PLANTA"
        assert data["evaluator_used"] == "RecyclableMaterialEvaluator"

        duplicate = client.post(
            "/api/v1/plant/packages/ECO-2026-AB12/process",
            json={
                "verified_weight_kg": 1.0,
                "verified_material": "PLASTICO",
                "is_contaminated": False,
                "operator_id": 1,
            },
        )
        assert duplicate.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_plant_contaminated_package_awards_zero_points():
    client, citizen_id = _setup_in_memory_plant()
    try:
        res = client.post(
            "/api/v1/plant/packages/ECO-2026-AB12/process",
            json={
                "verified_weight_kg": 3.0,
                "verified_material": "PLASTICO",
                "is_contaminated": True,
                "operator_id": 1,
                "observations": "Mezclado con residuos organicos",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["points_awarded"] == 0
        assert data["citizen_new_balance"] == 10
        assert data["is_contaminated"] is True
        assert data["evaluator_used"] == "ContaminatedRejectedEvaluator"
        assert client.get("/api/v1/plant/packages/NO-EXISTE").status_code == 404
    finally:
        app.dependency_overrides.clear()
